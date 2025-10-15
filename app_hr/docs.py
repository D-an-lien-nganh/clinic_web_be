from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from .serializers import HrUserProfileSerializer  # Adjust imports as needed

# Schema for HrUserProfileViewSet
def hr_management_schema():
    return extend_schema_view(
        list=extend_schema(
            tags=["app_hr"],
            summary="Danh sách hồ sơ nhân sự",
            description="Lấy danh sách tất cả hồ sơ nhân sự trong hệ thống với tùy chọn lọc.",
            parameters=[
                OpenApiParameter(
                    name='startDate',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Lọc hồ sơ theo ngày bắt đầu (YYYY-MM-DD)',
                    required=False
                ),
                OpenApiParameter(
                    name='endDate',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Lọc hồ sơ theo ngày kết thúc (YYYY-MM-DD)',
                    required=False
                ),
                OpenApiParameter(
                    name='searchTerm',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Tìm kiếm hồ sơ theo tên người dùng, email, số điện thoại hoặc chức danh',
                    required=False
                ),
                OpenApiParameter(
                    name='format',
                    type=str,
                    location=OpenApiParameter.QUERY,
                    description='Lọc hồ sơ theo định dạng (nếu có)',
                    required=False
                ),
            ],
            responses={
                200: OpenApiResponse(
                    description="Danh sách hồ sơ nhân sự phân trang",
                    response=HrUserProfileSerializer(many=True),
                    examples=[
                        OpenApiExample(
                            "Danh sách hồ sơ nhân sự",
                            value={
                                "count": 1,
                                "next": None,
                                "previous": None,
                                "results": [
                                    {
                                        "id": 1,
                                        "user_profile_user_username": "johndoe",
                                        "user_profile_user_email": "john@example.com",
                                        "user_profile_user_mobile_number": "1234567890",
                                        "user_profile_position_title": "Nhân viên HR",
                                        "created": "2025-03-03T12:00:00Z"
                                    }
                                ]
                            }
                        )
                    ]
                ),
                400: OpenApiResponse(description="Yêu cầu không hợp lệ do tham số sai"),
            }
        ),
        retrieve=extend_schema(
            tags=["app_hr"],
            summary="Chi tiết hồ sơ nhân sự",
            description="Lấy thông tin chi tiết của một hồ sơ nhân sự theo ID.",
            responses={
                200: OpenApiResponse(
                    description="Chi tiết hồ sơ nhân sự",
                    response=HrUserProfileSerializer,
                    examples=[
                        OpenApiExample(
                            "Chi tiết hồ sơ nhân sự",
                            value={
                                "id": 1,
                                "user_profile_user_username": "johndoe",
                                "user_profile_user_email": "john@example.com",
                                "user_profile_user_mobile_number": "1234567890",
                                "user_profile_position_title": "Nhân viên HR",
                                "created": "2025-03-03T12:00:00Z"
                            }
                        )
                    ]
                ),
                404: OpenApiResponse(description="Không tìm thấy hồ sơ nhân sự"),
            }
        ),
        create=extend_schema(
            tags=["app_hr"],
            summary="Tạo hồ sơ nhân sự mới",
            description="API để tạo một hồ sơ nhân sự mới.",
            request=HrUserProfileSerializer,
            responses={
                201: OpenApiResponse(
                    description="Hồ sơ nhân sự được tạo thành công",
                    response=HrUserProfileSerializer,
                    examples=[
                        OpenApiExample(
                            "Hồ sơ nhân sự mới",
                            value={
                                
                                "user": 103,
                                "user_profile": 1,
                                "contract_start": "2024-08-01",
                                "contract_end": "2025-08-01",
                                "contract_status": "AC",
                                "contract_type": "OF",
                                "start_date": "2022-06-15",
                                "level": "Senior Engineer"
                                

                            }
                        )
                    ]
                ),
                400: OpenApiResponse(description="Dữ liệu đầu vào không hợp lệ"),
            },
            examples=[
                OpenApiExample(
                    "Tạo hồ sơ nhân sự",
                    summary="Ví dụ tạo hồ sơ",
                    value={
                        
                        "user": 103,
                        "user_profile": 1,
                        "contract_start": "2024-08-01",
                        "contract_end": "2025-08-01",
                        "contract_status": "AC",
                        "contract_type": "OF",
                        "start_date": "2022-06-15",
                        "level": "Senior Engineer"
                        

                    }
                )
            ]
        ),
        update=extend_schema(
            tags=["app_hr"],
            summary="Cập nhật hồ sơ nhân sự",
            description="API để cập nhật thông tin hồ sơ nhân sự theo ID.",
            request=HrUserProfileSerializer,
            responses={
                200: OpenApiResponse(
                    description="Hồ sơ nhân sự được cập nhật thành công",
                    response=HrUserProfileSerializer
                ),
                400: OpenApiResponse(description="Dữ liệu đầu vào không hợp lệ"),
                404: OpenApiResponse(description="Không tìm thấy hồ sơ nhân sự"),
            }
        ),
        partial_update=extend_schema(
            tags=["app_hr"],
            summary="Cập nhật một phần hồ sơ nhân sự",
            description="API để cập nhật một phần thông tin hồ sơ nhân sự theo ID.",
            request=HrUserProfileSerializer,
            responses={
                200: OpenApiResponse(
                    description="Hồ sơ nhân sự được cập nhật một phần thành công",
                    response=HrUserProfileSerializer
                ),
                400: OpenApiResponse(description="Dữ liệu đầu vào không hợp lệ"),
                404: OpenApiResponse(description="Không tìm thấy hồ sơ nhân sự"),
            }
        ),
        destroy=extend_schema(
            tags=["app_hr"],
            summary="Xóa hồ sơ nhân sự",
            description="API để xóa một hồ sơ nhân sự.",
            responses={
                204: OpenApiResponse(description="Hồ sơ nhân sự đã được xóa thành công"),
                404: OpenApiResponse(description="Không tìm thấy hồ sơ nhân sự"),
            }
        )
    )