import sys
import os

# src 폴더를 파이썬 경로에 추가하여 모듈을 찾을 수 있도록 합니다.
# 이 코드는 main.py가 프로젝트 루트에 있다는 가정 하에 동작합니다.
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# src 폴더의 crawler와 parser.excel_to_db에서 각 메인 함수를 가져옵니다.
from crawler import run_crawler
from excel_to_db import main as run_parser

def main_process():
    """
    크롤링부터 데이터베이스 적재까지 전체 프로세스를 실행합니다.
    """
    print("="*50)
    print(" 데이터 수집 및 적재 자동화 프로세스를 시작합니다. ")
    print("="*50)

    try:
        # --- 1단계: 웹 크롤링 및 엑셀 파일 다운로드 ---
        print("\n[1/2] 웹사이트에서 데이터 크롤링을 시작합니다...")
        # run_crawler 함수는 성공 시 True, 실패 시 False를 반환합니다.
        is_crawling_success = run_crawler()

        if not is_crawling_success:
            print("\n!! 크롤링 단계에서 오류가 발생하여 전체 프로세스를 중단합니다.")
            return

        print("\n✅ 크롤링 및 파일 다운로드가 성공적으로 완료되었습니다.")

        # --- 2단계: 엑셀 파일 파싱 및 DB 적재 ---
        print("\n[2/2] 다운로드한 파일의 파싱 및 DB 적재를 시작합니다...")
        run_parser()

        print("\n" + "="*50)
        print("🎉 모든 프로세스가 성공적으로 완료되었습니다. 🎉")
        print("="*50)

    except Exception as e:
        print(f"\n!! 메인 프로세스 실행 중 예상치 못한 오류가 발생했습니다: {e}")

if __name__ == '__main__':
    main_process()