from rest_framework import serializers
from .models import Address, User    

class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'role']

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            role=validated_data['role']
        )                   
        return user
    
class userloginsSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'password']
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        user = User.objects.filter(email=email).first()
        if user and user.check_password(password):
            data['user'] = user
            return data
        raise serializers.ValidationError("Invalid email or password.")
        
        
        
class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'role', 'first_name',
        'last_name', 'phone_number', 'profile_picture', 'email_verified']  
        read_only_fields = ['id', 'email_verified']  
        
        
class AddressSerializer(serializers.ModelSerializer):

    class Meta:
        model = Address
        fields = ['id', 'user', 'address_line', 'city', 'state', 'postal_code', 'country'] 
        read_only_fields = ['user', 'created_at', 'updated_at' ] 
        
        
         
        
    
    