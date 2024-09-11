- AI-KMS를 구현하기 전에 프로토타이핑한 기능
- document를 upload하여 로컬 벡터db에 임베딩처리
- 대시보드, pdf parser등 테스트삼아 구현

1. QA_chat.py : 파일임베딩 및 chat
2. pdf_parser.py: pdf import 테스트
3. kms_embed.py: kms db를 읽어 임베딩, 임베딩이력, 대시보드

4. Palette_kms: ai검색 api호출 => streamlit_aikms로 이동
