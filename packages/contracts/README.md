# Integration Contracts

Nơi lưu các hợp đồng giao tiếp dùng chung giữa mobile, core API và AI service.

Nội dung dự kiến:

```text
contracts/
├── openapi/          # Đặc tả API công khai của core-api
├── schemas/          # JSON Schema cho request/response AI
├── examples/         # Request và response mẫu
└── errors/           # Quy ước mã lỗi
```

Mọi thay đổi làm ảnh hưởng cấu trúc request hoặc response phải được cập nhật
tại đây trước khi tích hợp.
