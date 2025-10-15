# schemas_accounting.py
from drf_spectacular.utils import (
    extend_schema, extend_schema_view, OpenApiParameter, OpenApiExample
)
from drf_spectacular.types import OpenApiTypes

from .serializers import (
    SupplierProductDebtSerializer, ProductDebtDetailSerializer,
    SupplierFacilityDebtSerializer, FacilityDebtDetailSerializer
)

# ---------- SupplierProductDebt ----------
def supplier_product_debt_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách công nợ SẢN PHẨM theo nhà cung cấp",
            description=(
                "Trả về các đầu sổ công nợ SẢN PHẨM (per-supplier). "
                "Mỗi record đại diện khoản phải trả cho NCC, tích lũy từ các phiếu nhập **product**.\n\n"
                "Lưu ý: Tổng nợ và còn nợ có thể được cache/cập nhật bằng signals hoặc tính động tuỳ triển khai."
            ),
            parameters=[
                OpenApiParameter(name="supplier", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                                 description="Filter theo ID nhà cung cấp"),
            ],
            responses={200: SupplierProductDebtSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Ví dụ list",
                    description="Danh sách công nợ SP",
                    value=[
                        {
                            "id": 1,
                            "created": "2025-08-01T05:00:00Z",
                            "user": 2,
                            "supplier": 1,
                            "supplier_name": "NCC A",
                            "total_amount": "150000000.00",
                            "total_paid": "100000000.00",
                            "remaining": "50000000.00"
                        }
                    ],
                )
            ],
        ),
        retrieve=extend_schema(
            summary="Xem chi tiết 1 đầu sổ công nợ SẢN PHẨM",
            responses={200: SupplierProductDebtSerializer},
            examples=[
                OpenApiExample(
                    name="Ví dụ retrieve",
                    value={
                        "id": 1,
                        "created": "2025-08-01T05:00:00Z",
                        "user": 2,
                        "supplier": 1,
                        "supplier_name": "NCC A",
                        "total_amount": "150000000.00",
                        "total_paid": "100000000.00",
                        "remaining": "50000000.00"
                    },
                )
            ],
        ),
        create=extend_schema(
            summary="Tạo đầu sổ công nợ SẢN PHẨM",
            description="Tạo mới đầu sổ công nợ SP cho một NCC.",
            request=SupplierProductDebtSerializer,
            responses={201: SupplierProductDebtSerializer},
            examples=[
                OpenApiExample(
                    name="Request tạo đầu sổ SP",
                    request_only=True,
                    value={
                        "supplier": 1,
                        "total_amount": "0.00"  # hoặc để 0 nếu bạn cập nhật bằng StockIn
                    },
                ),
                OpenApiExample(
                    name="Response tạo đầu sổ SP",
                    response_only=True,
                    value={
                        "id": 2,
                        "created": "2025-08-02T01:23:45Z",
                        "user": 2,
                        "supplier": 1,
                        "supplier_name": "NCC A",
                        "total_amount": "0.00",
                        "total_paid": "0.00",
                        "remaining": "0.00"
                    },
                ),
            ],
        ),
        update=extend_schema(
            summary="Cập nhật đầu sổ công nợ SẢN PHẨM",
            request=SupplierProductDebtSerializer,
            responses={200: SupplierProductDebtSerializer},
            examples=[
                OpenApiExample(
                    name="PATCH/PUT đầu sổ SP",
                    request_only=True,
                    value={"total_amount": "200000000.00"},
                )
            ],
        ),
        destroy=extend_schema(
            summary="Xoá đầu sổ công nợ SẢN PHẨM",
            responses={204: None},
        ),
    )


# ---------- ProductDebtDetail ----------
def product_debt_detail_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách thanh toán công nợ SẢN PHẨM",
            description="Chỉ trả về các thanh toán gắn với **StockIn.product != null** và **StockIn.facility == null**.",
            parameters=[
                OpenApiParameter(name="supplier", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="ID NCC"),
                OpenApiParameter(name="product",  type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="ID sản phẩm"),
                OpenApiParameter(name="stock_in", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="ID phiếu nhập"),
                OpenApiParameter(name="method",   type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Phương thức: cash/transfer"),
            ],
            responses={200: ProductDebtDetailSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Ví dụ list",
                    value=[
                        {
                            "id": 10,
                            "created": "2025-08-03T04:00:00Z",
                            "user": 5,
                            "code": "PMT-ABCD12",
                            "method": "transfer",
                            "stock_in": 1,
                            "supplier": 1,
                            "supplier_name": "NCC A",
                            "product_name": "Laptop Pro 14",
                            "paid_amount": "100000000.00",
                            "note": "Đợt 1"
                        }
                    ],
                )
            ],
        ),
        retrieve=extend_schema(
            summary="Xem chi tiết 1 thanh toán công nợ SẢN PHẨM",
            responses={200: ProductDebtDetailSerializer},
        ),
        create=extend_schema(
            summary="Tạo thanh toán công nợ SẢN PHẨM",
            description=(
                "Tạo phiếu thanh toán gắn với **StockIn thuộc loại SẢN PHẨM**. "
                "Model sẽ validate: `paid_amount > 0`, và `StockIn.product != null`."
            ),
            request=ProductDebtDetailSerializer,
            responses={201: ProductDebtDetailSerializer},
            examples=[
                OpenApiExample(
                    name="Request tạo thanh toán SP",
                    request_only=True,
                    value={
                        "stock_in": 1,
                        "method": "cash",
                        "paid_amount": "50000000.00",
                        "note": "Thanh toán đợt 2"
                    },
                ),
                OpenApiExample(
                    name="Response tạo thanh toán SP",
                    response_only=True,
                    value={
                        "id": 11,
                        "created": "2025-08-03T05:00:00Z",
                        "user": 5,
                        "code": "PMT-XYZ789",
                        "method": "cash",
                        "stock_in": 1,
                        "supplier": 1,
                        "supplier_name": "NCC A",
                        "product_name": "Laptop Pro 14",
                        "paid_amount": "50000000.00",
                        "note": "Thanh toán đợt 2"
                    },
                ),
            ],
        ),
        update=extend_schema(
            summary="Cập nhật thanh toán công nợ SẢN PHẨM",
            request=ProductDebtDetailSerializer,
            responses={200: ProductDebtDetailSerializer},
        ),
        destroy=extend_schema(
            summary="Xoá thanh toán công nợ SẢN PHẨM",
            responses={204: None},
        ),
    )


# ---------- SupplierFacilityDebt ----------
def supplier_facility_debt_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách công nợ VẬT TƯ theo nhà cung cấp",
            description="Đầu sổ công nợ VẬT TƯ (per-supplier), tích lũy từ các phiếu nhập **facility**.",
            parameters=[
                OpenApiParameter(name="supplier", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY,
                                 description="Filter theo ID nhà cung cấp"),
            ],
            responses={200: SupplierFacilityDebtSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Ví dụ list",
                    value=[
                        {
                            "id": 3,
                            "created": "2025-08-02T02:00:00Z",
                            "user": 2,
                            "supplier": 1,
                            "supplier_name": "NCC A",
                            "total_amount": "30000000.00",
                            "total_paid": "30000000.00",
                            "remaining": "0.00"
                        }
                    ],
                )
            ],
        ),
        retrieve=extend_schema(
            summary="Xem chi tiết 1 đầu sổ công nợ VẬT TƯ",
            responses={200: SupplierFacilityDebtSerializer},
        ),
        create=extend_schema(
            summary="Tạo đầu sổ công nợ VẬT TƯ",
            description="Tạo mới đầu sổ công nợ VT cho một NCC.",
            request=SupplierFacilityDebtSerializer,
            responses={201: SupplierFacilityDebtSerializer},
            examples=[
                OpenApiExample(
                    name="Request tạo đầu sổ VT",
                    request_only=True,
                    value={"supplier": 1, "total_amount": "0.00"},
                ),
                OpenApiExample(
                    name="Response tạo đầu sổ VT",
                    response_only=True,
                    value={
                        "id": 4,
                        "created": "2025-08-02T03:00:00Z",
                        "user": 2,
                        "supplier": 1,
                        "supplier_name": "NCC A",
                        "total_amount": "0.00",
                        "total_paid": "0.00",
                        "remaining": "0.00"
                    },
                ),
            ],
        ),
        update=extend_schema(
            summary="Cập nhật đầu sổ công nợ VẬT TƯ",
            request=SupplierFacilityDebtSerializer,
            responses={200: SupplierFacilityDebtSerializer},
        ),
        destroy=extend_schema(
            summary="Xoá đầu sổ công nợ VẬT TƯ",
            responses={204: None},
        ),
    )


# ---------- FacilityDebtDetail ----------
def facility_debt_detail_schema_view():
    return extend_schema_view(
        list=extend_schema(
            summary="Danh sách thanh toán công nợ VẬT TƯ",
            description="Chỉ trả về các thanh toán gắn với **StockIn.facility != null** và **StockIn.product == null**.",
            parameters=[
                OpenApiParameter(name="supplier", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="ID NCC"),
                OpenApiParameter(name="facility", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="ID vật tư"),
                OpenApiParameter(name="stock_in", type=OpenApiTypes.INT, location=OpenApiParameter.QUERY, description="ID phiếu nhập"),
                OpenApiParameter(name="method",   type=OpenApiTypes.STR, location=OpenApiParameter.QUERY, description="Phương thức: cash/transfer"),
            ],
            responses={200: FacilityDebtDetailSerializer(many=True)},
            examples=[
                OpenApiExample(
                    name="Ví dụ list",
                    value=[
                        {
                            "id": 20,
                            "created": "2025-08-02T12:00:00Z",
                            "user": 5,
                            "code": "PMT-FAC-001",
                            "method": "transfer",
                            "stock_in": 7,
                            "supplier": 1,
                            "supplier_name": "NCC A",
                            "facility_name": "Micro không dây",
                            "paid_amount": "30000000.00",
                            "note": "Thanh toán đủ"
                        }
                    ],
                )
            ],
        ),
        retrieve=extend_schema(
            summary="Xem chi tiết 1 thanh toán công nợ VẬT TƯ",
            responses={200: FacilityDebtDetailSerializer},
        ),
        create=extend_schema(
            summary="Tạo thanh toán công nợ VẬT TƯ",
            description=(
                "Tạo phiếu thanh toán gắn với **StockIn thuộc loại VẬT TƯ**. "
                "Model sẽ validate: `paid_amount > 0`, và `StockIn.facility != null`."
            ),
            request=FacilityDebtDetailSerializer,
            responses={201: FacilityDebtDetailSerializer},
            examples=[
                OpenApiExample(
                    name="Request tạo thanh toán VT",
                    request_only=True,
                    value={
                        "stock_in": 7,
                        "method": "transfer",
                        "paid_amount": "30000000.00",
                        "note": "Thanh toán đủ"
                    },
                ),
                OpenApiExample(
                    name="Response tạo thanh toán VT",
                    response_only=True,
                    value={
                        "id": 21,
                        "created": "2025-08-02T12:30:00Z",
                        "user": 5,
                        "code": "PMT-FAC-002",
                        "method": "transfer",
                        "stock_in": 7,
                        "supplier": 1,
                        "supplier_name": "NCC A",
                        "facility_name": "Micro không dây",
                        "paid_amount": "30000000.00",
                        "note": "Thanh toán đủ"
                    },
                ),
            ],
        ),
        update=extend_schema(
            summary="Cập nhật thanh toán công nợ VẬT TƯ",
            request=FacilityDebtDetailSerializer,
            responses={200: FacilityDebtDetailSerializer},
        ),
        destroy=extend_schema(
            summary="Xoá thanh toán công nợ VẬT TƯ",
            responses={204: None},
        ),
    )
