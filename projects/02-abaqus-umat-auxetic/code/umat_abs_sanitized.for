C ======================================================================
C PORTFOLIO-SANITIZED COURSEWORK IMPLEMENTATION
C Author: Yasamin Shahbazi
C Project: Hyperelastic ABS UMAT and re-entrant auxetic compression
C
C This file preserves the constitutive implementation demonstrated in the
C project report. Abaqus databases, journals, institution-specific files,
C and the externally credited general matrix-inversion routine are omitted.
C The latter is replaced below by a compact analytical 3x3 inverse.
C
C Verification status: the original project compared this UMAT against
C published tensile data and Abaqus' native polynomial hyperelastic model.
C This sanitized copy has not been recompiled in the current environment.
C ======================================================================
      SUBROUTINE UMAT(STRESS,STATEV,DDSDDE,SSE,SPD,SCD,
     1 RPL,DDSDDT,DRPLDE,DRPLDT,
     2 STRAN,DSTRAN,TIME,DTIME,TEMP,DTEMP,PREDEF,DPRED,CMNAME,
     3 NDI,NSHR,NTENS,NSTATV,PROPS,NPROPS,COORDS,DROT,PNEWDT,
     4 CELENT,DFGRD0,DFGRD1,NOEL,NPT,LAYER,KSPT,JSTEP,KINC)
C
      INCLUDE 'ABA_PARAM.INC'
C
      CHARACTER*80 CMNAME
      DIMENSION STRESS(NTENS+3),STATEV(NSTATV),
     1 DDSDDE(NTENS,NTENS),DDSDDT(NTENS),DRPLDE(NTENS),
     2 STRAN(NTENS),DSTRAN(NTENS),TIME(2),PREDEF(1),DPRED(1),
     3 PROPS(NPROPS),COORDS(3),DROT(3,3),DFGRD0(3,3),DFGRD1(3,3),
     4 JSTEP(4)


      Real*8 :: A1,A2,A3,A4,Jacob,Incomp
      Real*8 :: RCG(NDI,NDI),RCGINV(NDI,NDI),RCG2(NDI,NDI),Unit(NDI,NDI)
      Real*8 :: SPstrs(NDI,NDI),dI1dc(NDI,NDI),dI2dc(NDI,NDI)
      Real*8 :: dI3dc(NDI,NDI)
      Real*8 :: Cauchy(NDI,NDI),CSE(NDI,NDI,NDI,NDI)
      Real*8 :: CCa(NDI,NDI,NDI,NDI)
      Real*8 :: I1,I2,I3,TraceC2,W
      Real*8 :: dWdI1,dWdI2,dWdI3,dWdI1I1,dWdI2I2,dWdI3I3
      Real*8 :: dWdI1I2,dWdI1I3,dWdI2I3
      Real*8 :: dij,dkl,dik,djl,dil,djk,UI4
      Integer :: i,j,k,l,m,n,mp,mq,ia,ja

      A1= props(1); A2= props(2);A3= props(3); A4= props(4); 
      Incomp= props(5);
      
!     ***************************Identity Matrix*******************************     
      Unit=0.D0
      Unit(1,1)=1.D0; Unit(2,2)=1.D0; 
      IF(NDI==3) Unit(3,3)=1.D0
      
!     **********************************Jacobin*******************************         
        Jacob=(DFGRD1(1,1)*DFGRD1(2,2)*DFGRD1(3,3)+
     1         DFGRD1(1,2)*DFGRD1(2,3)*DFGRD1(3,1)+
     2         DFGRD1(1,3)*DFGRD1(2,1)*DFGRD1(3,2))-
     3         (DFGRD1(1,1)*DFGRD1(2,3)*DFGRD1(3,2)+
     4         DFGRD1(1,2)*DFGRD1(2,1)*DFGRD1(3,3)+
     5         DFGRD1(1,3)*DFGRD1(2,2)*DFGRD1(3,1))      
      
!     ******************************Right Cauchy-Green*************************
       RCG =Matmul(Transpose(DFGRD1),DFGRD1)   
       RCG2=Matmul(RCG,RCG) 
       
!     ********************************Invariants of C**************************
       I1=RCG(1,1)+RCG(2,2)+RCG(3,3)
       
       TraceC2=RCG2(1,1)+RCG2(2,2)+RCG2(3,3)
       I2=(I1**2.D0-TraceC2)/2.D0
       
       I3=Jacob**2.D0
!***********************Hyperelastic strain energy Derivatives*****************
       W=A1*(I1-3.D0)+A2*(I2-3.D0)+A3*(I1-3.D0)**2.D0+A4*(I2-3.D0)**2.D0
     1 +Incomp*(I3-1.D0)**2.D0;
      
       
!      *************First Derivatives************       
       dWdI1=A1+2*A3*(I1-3.D0);
       
       dWdI2=A2+2*A4*(I2-3.D0);
       
       dWdI3=2.D0*Incomp*(I3-1.D0);
       
!      *************Second Derivatives************        
       dWdI1I1=2.D0*A3
       
       dWdI2I2=2.D0*A4
       
       dWdI3I3=2.D0*Incomp
       
       dWdI1I2=0.D0
       
       dWdI1I3=0.D0
       
       dWdI2I3=0.D0
       
!*****************************Second-Piola Kirchhoff Stress********************
       dI1dc=Unit
       dI2dc=I1*Unit-RCG 
       
       CALL Inv3(RCG,RCGINV)
       dI3dc=I3*RCGINV 
       
       SPstrs=dWdI1*dI1dc+dWdI2*dI2dc+dWdI3*dI3dc
       
       SPstrs=2.D0*SPstrs        
       
!**********************************Cauchy Stress Update************************ 
      Cauchy=Matmul(DFGRD1,Matmul(SPstrs,Transpose(DFGRD1)))/Jacob
       
       STRESS(1)=Cauchy(1,1); STRESS(2)=Cauchy(2,2); 
       STRESS(3)=Cauchy(3,3);
       STRESS(4)=Cauchy(1,2); STRESS(5)=Cauchy(1,3); 
       STRESS(6)=Cauchy(2,3);
       
!********************************Second Piola Jacobian Matrix******************       
      Do 5 i=1,NDI
       Do 5 j=1,NDI
        Do 5 k=1,NDI
         Do 5 l=1,NDI
          dij=0.D0; dkl=0.D0; dik=0.D0; djl=0.D0; dil=0.D0; djk=0.D0
          IF(i==j)dij=1.D0
          IF(k==l)dkl=1.D0
          IF(i==k)dik=1.D0 
          IF(j==l)djl=1.D0
          IF(i==l)dil=1.D0
          IF(j==k)djk=1.D0
          UI4=0.5D0*(dik*djl+dil*djk)
  
     
       CSE(i,j,k,l)=(dWdI1I1+I1*dWdI1I2+dWdI2)*dij*dkl+
     1                (I1*dWdI2I2+dWdI1I2)*dij*(I1*dkl-RCG(k,l))+
     2                (dWdI1I3+I1*dWdI2I3)*I3*dij*RCGINV(k,l)-
     3                (dWdI1I2+I1*dWdI2I2)*RCG(i,j)*dkl+
     4                dWdI2I2*RCG(i,j)*RCG(k,l)-
     5                dWdI2I3*I3*RCG(i,j)*RCGINV(k,l)-
     6                dWdI2*UI4+
     7               (I3*dWdI3+dWdI3I3*I3**2.D0)*RCGINV(i,j)*RCGINV(k,l)+
     8                (I3*dWdI1I3+I1*I3*dWdI2I3)*RCGINV(i,j)*dkl-
     9                I3*dWdI2I3*RCGINV(i,j)*RCG(k,l)-
     1                0.5D0*dWdI3*I3*
     2                 (RCGINV(i,k)*RCGINV(j,l)+RCGINV(i,l)*RCGINV(j,k))
5      Continue    
      CSE=4.D0*CSE
!*********************************Cauchy Jacobian Matrix***********************
      CCa=0.D0
       Do 10 i=1,NDI
       Do 10 j=1,NDI
       Do 10 k=1,NDI
       Do 10 l=1,NDI
        Do 10 m=1,NDI
        Do 10 n=1,NDI
        Do 10 mp=1,NDI
        Do 10 mq=1,NDI
         CCa(i,j,k,l)=CCa(i,j,k,l)+DFGRD1(i,m)*DFGRD1(j,n)*DFGRD1(k,mp)
     1                  *DFGRD1(l,mq)*CSE(m,n,mp,mq)
10     Continue 

       Do 12 i=1,NDI
       Do 12 j=1,NDI
       Do 12 k=1,NDI
       Do 12 l=1,NDI
        dij=0.D0; dkl=0.D0; dik=0.D0; djl=0.D0; dil=0.D0; djk=0.D0
        IF(i==j)dij=1.D0
        IF(k==l)dkl=1.D0
        IF(i==k)dik=1.D0 
        IF(j==l)djl=1.D0
        IF(i==l)dil=1.D0
        IF(j==k)djk=1.D0       

         CCa(i,j,k,l)=CCa(i,j,k,l)+0.5D0*Jacob*(dik*Cauchy(j,l)+djl*
     1                   Cauchy(i,k)+dil*Cauchy(j,k)+djk*Cauchy(i,l))
12     Continue  
      
!***********************************DDSDDE Update******************************      
      Do 15 ia=1,NTENS
       Do 15 ja=1,NTENS
        Call Voigt(ia,i,j)
        Call Voigt(ja,k,l)
        DDSDDE(ia,ja)=CCa(i,j,k,l)/Jacob
!        IF(ia>NDI) DDSDDE(ia,ja)=2.0*DDSDDE(ia,ja)
!        IF(ja>NDI) DDSDDE(ia,ja)=2.0*DDSDDE(ia,ja)
15    Continue      

!        Write(*,11) ((DDSDDE(ia,ja),ia=1,6),ja=1,6)
!        Write(*,11) (STRESS(ia),ia=1,6)        


      Return
      End
      
!******************************************************************************      
!************************************Subroutine Voigt************************  
! *****************************************************************************       
!******************************************************************************
      Subroutine Voigt(ia,i,j)

      Integer ia,i,j
     
      If(ia==1)Then
       i=1; j=1
      End If
      
      If(ia==2)Then
       i=2; j=2
      End If
      
      If(ia==3)Then
       i=3; j=3
      End If
      
      If(ia==4)Then
       i=1; j=2
      End If
      
      If(ia==5)Then
       i=1; j=3
      End If
      
      If(ia==6)Then
       i=2; j=3 
      End If
      
      End Subroutine Voigt      
!******************************************************************************
! Analytical inverse for the 3x3 right Cauchy-Green tensor.
! This local implementation replaces a third-party general LU routine.
!******************************************************************************
      Subroutine Inv3(A,Ainv)

      Real*8 :: A(3,3),Ainv(3,3),detA

      detA=A(1,1)*(A(2,2)*A(3,3)-A(2,3)*A(3,2))
     1    -A(1,2)*(A(2,1)*A(3,3)-A(2,3)*A(3,1))
     2    +A(1,3)*(A(2,1)*A(3,2)-A(2,2)*A(3,1))

      If(Abs(detA).LT.1.D-14) Then
       Write(6,*) 'UMAT error: singular right Cauchy-Green tensor.'
       Call XIT
      End If

      Ainv(1,1)=(A(2,2)*A(3,3)-A(2,3)*A(3,2))/detA
      Ainv(1,2)=(A(1,3)*A(3,2)-A(1,2)*A(3,3))/detA
      Ainv(1,3)=(A(1,2)*A(2,3)-A(1,3)*A(2,2))/detA
      Ainv(2,1)=(A(2,3)*A(3,1)-A(2,1)*A(3,3))/detA
      Ainv(2,2)=(A(1,1)*A(3,3)-A(1,3)*A(3,1))/detA
      Ainv(2,3)=(A(1,3)*A(2,1)-A(1,1)*A(2,3))/detA
      Ainv(3,1)=(A(2,1)*A(3,2)-A(2,2)*A(3,1))/detA
      Ainv(3,2)=(A(1,2)*A(3,1)-A(1,1)*A(3,2))/detA
      Ainv(3,3)=(A(1,1)*A(2,2)-A(1,2)*A(2,1))/detA

      Return
      End Subroutine Inv3

      
