from google import genai

client = genai.Client(api_key="API_KEY")

print("Đang tìm các model hỗ trợ Live API...")

# Lấy danh sách tất cả model
for model in client.models.list():
    if "gemini" in model.name:
         print(f"Model: {model.name} | Display Name: {model.display_name}")

print("\n--- HƯỚNG DẪN ---")
print("Hãy tìm model nào có tên chứa 'gemini-2.0-flash-exp' hoặc tương tự.")