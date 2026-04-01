from django.shortcuts import render
from django.contrib.auth import login
from rest_framework import generics , status, permissions
from rest_framework.response import Response
from .models import Address, User
from .serializers import AddressSerializer, RegisterSerializer, UserSerializer, userloginsSerializer 
from rest_framework_simplejwt.tokens import RefreshToken


class RegisterView(generics.CreateAPIView):

    queryset = User.objects.all()
    serializer_class = RegisterSerializer   
    permission_classes = [permissions.AllowAny ]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": RegisterSerializer(user, context=self.get_serializer_context()).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            "message": "User registered successfully."
        }, status=status.HTTP_201_CREATED)  
        
    
class LoginView(generics.CreateAPIView):

    serializer_class = userloginsSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Allow DRF browsable API login state after successful API login.
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)

        refresh = RefreshToken.for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'message': 'Login successful.'
        }, status=status.HTTP_200_OK)
        
        
class UserProfileView(generics.RetrieveUpdateAPIView):

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    

class AdressListCreateView(generics.ListCreateAPIView):

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
class AddressDetailView(generics.RetrieveUpdateDestroyAPIView):

    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Address.objects.filter(user=self.request.user)
        
        

    