from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from common.permissions import IsAdminRole
from common.rbac import Perm
from common.rbac.checker import PermissionChecker, get_user_permissions
from apps.employees.serializers import EmployeeDetailSerializer

from .models import SecurityLog
from .audit_models import AuditLog
from .serializers import AuditLogSerializer, RegisterSerializer, SecurityLogSerializer, UserSerializer
from .services import log_security_event
from common.throttling import LoginRateThrottle, RegisterRateThrottle


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]
    throttle_classes = [RegisterRateThrottle, AnonRateThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_security_event(request, SecurityLog.EventType.REGISTER, user=user)
        return Response(
            {
                "success": True,
                "message": "Тіркелу сәтті аяқталды.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle, AnonRateThrottle]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            log_security_event(request, SecurityLog.EventType.LOGIN_FAILED, metadata={"username": request.data.get("username")})
            raise

        user = serializer.user
        log_security_event(request, SecurityLog.EventType.LOGIN_SUCCESS, user=user)
        return Response(
            {
                "success": True,
                "access": serializer.validated_data["access"],
                "refresh": serializer.validated_data["refresh"],
                "user": UserSerializer(user).data,
                "permissions": get_user_permissions(user),
            }
        )


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            log_security_event(request, SecurityLog.EventType.TOKEN_REFRESH)
        return response


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        employee_profile = None
        if hasattr(request.user, "employee_profile"):
            employee_profile = EmployeeDetailSerializer(
                request.user.employee_profile,
                context={"request": request},
            ).data
        return Response(
            {
                "success": True,
                "user": UserSerializer(request.user).data,
                "employee_profile": employee_profile,
                "permissions": get_user_permissions(request.user),
                "scope": {
                    "role": request.user.role,
                    "department_id": PermissionChecker(request.user).department_id(),
                },
            }
        )

    def patch(self, request):
        allowed_fields = {"first_name", "last_name", "email", "phone"}
        profile_data = {
            key: value
            for key, value in request.data.items()
            if key in allowed_fields
        }
        serializer = UserSerializer(request.user, data=profile_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "user": serializer.data})


class SecurityLogListView(generics.ListAPIView):
    serializer_class = SecurityLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return SecurityLog.objects.select_related("user").all()[:500]

    def list(self, request, *args, **kwargs):
        from common.rbac import Perm

        if not PermissionChecker(request.user).has(Perm.SECURITY_VIEW_LOGS):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Недостаточно прав доступа.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "results": serializer.data})


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return AuditLog.objects.select_related("actor").all()[:500]

    def list(self, request, *args, **kwargs):
        if not PermissionChecker(request.user).has(Perm.SECURITY_VIEW_LOGS):
            from rest_framework.exceptions import PermissionDenied

            raise PermissionDenied("Рұқсат жеткіліксіз.")
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "results": serializer.data})
