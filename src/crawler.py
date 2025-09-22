import os
import time
from datetime import date, timedelta

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select


# --- 3. 기능별 함수 정의 ---
def select_date(driver, wait, date_label, target_date):
    """'시작일', '종료일' 필드의 날짜를 설정하는 함수"""
    try:
        print(f"\n▶ '{date_label}' 필드에서 날짜 [{target_date}]를 설정합니다.")
        year_xpath = f"//b[contains(text(), '{date_label}')]/following::select[1]"
        month_xpath = f"//b[contains(text(), '{date_label}')]/following::select[2]"
        day_xpath = f"//b[contains(text(), '{date_label}')]/following::select[3]"

        Select(wait.until(EC.presence_of_element_located((By.XPATH, year_xpath)))).select_by_value(
            f"{target_date.year}년")
        time.sleep(0.5)
        Select(wait.until(EC.presence_of_element_located((By.XPATH, month_xpath)))).select_by_value(
            f"{target_date.month:02d}월")
        time.sleep(0.5)
        Select(wait.until(EC.presence_of_element_located((By.XPATH, day_xpath)))).select_by_value(
            f"{target_date.day:02d}일")
        print(f"  - 날짜 [{target_date}] 선택 완료.")
        time.sleep(1)
    except Exception as e:
        print(f"오류 발생: '{date_label}' 날짜 선택 중 문제가 발생했습니다.")
        raise e


def select_pummok(driver, wait, item_text):
    """'품목' 드롭다운을 위한 전용 함수"""
    try:
        print(f"\n▶ '품목' 드롭다운에서 '{item_text}' 항목을 선택합니다.")
        select_xpath = "//div[contains(@class, 'inlinelabeldiv') and contains(text(), '품목')]/ancestor::label/following-sibling::div//select"
        select_element = wait.until(EC.presence_of_element_located((By.XPATH, select_xpath)))
        Select(select_element).select_by_visible_text(item_text)
        print(f"  - '{item_text}' 선택 완료.")
        time.sleep(2)
    except Exception as e:
        print(f"오류 발생: '품목' 선택 중 문제가 발생했습니다.")
        raise e


def select_filter_option(driver, wait, filter_title, option_text, search_required=False):
    """'품종', '거래단위' 등 Qlik 필터를 처리하는 범용 함수"""
    try:
        print(f"\n▶ '{filter_title}' 필터에서 '{option_text}' 옵션을 선택합니다.")

        # 1. 클릭할 필터 헤더 찾기
        filter_header_xpath = f"//span[@title='{filter_title}']/ancestor::div[contains(@class, 'qv-collapsed-listbox')]"
        header_element = wait.until(EC.element_to_be_clickable((By.XPATH, filter_header_xpath)))
        header_element.click()
        time.sleep(1)

        # 검색이 필요한 경우, 검색창에 값을 입력
        if search_required:
            print(f"  - '{option_text}' 항목을 검색합니다...")
            search_box_xpath = "//div[contains(@class, 'qv-listbox-popover')]//input"
            search_box = wait.until(EC.presence_of_element_located((By.XPATH, search_box_xpath)))
            search_box.send_keys(option_text)
            time.sleep(1)  # 검색 결과가 나타날 때까지 잠시 대기

        # 2. 열린 목록에서 옵션 찾아 클릭
        option_xpath = f"//div[contains(@class, 'qv-listbox-popover')]//span[@title='{option_text}']"
        option_item = wait.until(EC.element_to_be_clickable((By.XPATH, option_xpath)))
        option_item.click()
        time.sleep(1)

        # ★★★ 수정된 부분 ★★★
        # 3. 확인 버튼(녹색 체크 표시)을 클릭하여 선택을 확정합니다.
        confirm_button_xpath = "//button[@title='선택 확인']"
        wait.until(EC.element_to_be_clickable((By.XPATH, confirm_button_xpath))).click()
        print(f"  - '{option_text}' 선택 확정.")
        time.sleep(2)

    except Exception as e:
        print(f"오류 발생: '{filter_title}' 필드에서 '{option_text}' 선택 중 문제가 발생했습니다.")
        raise e


# --- 4. 자동화 실행 ---
def run_crawler():

    driver = None
    is_success = False

    env = os.getenv("EXECUTION_ENV", "local")
    print(f"--- 실행 환경: {env} ---")
    try:

        # --- 1. 날짜 계산 ---
        today = date.today()
        start_date = today - timedelta(days=3)
        end_date = today - timedelta(days=2)

        print(f"▶ 기준 날짜: {today}")
        print(f"▶ 설정할 시작 날짜: {start_date}")
        print(f"▶ 설정할 종료 날짜: {end_date}")

        # --- 2. 웹 드라이버 설정 ---
        # 현재 스크립트 파일이 있는 디렉토리(src)를 찾습니다.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # 그 상위 디렉토리(프로젝트 루트)를 찾습니다.
        project_root = os.path.dirname(current_dir)
        # 프로젝트 루트 하위에 'output' 폴더 경로를 설정합니다.
        DOWNLOAD_DIR = os.path.join(project_root, "output")
        # 폴더가 존재하지 않으면 생성합니다.
        if not os.path.exists(DOWNLOAD_DIR):
            os.makedirs(DOWNLOAD_DIR)
        print(f"▶ 파일이 저장될 경로: {DOWNLOAD_DIR}")

        # <<<<<< 3. 크롬 옵션 설정 >>>>>>
        chrome_options = webdriver.ChromeOptions()
        prefs = {
            "download.default_directory": DOWNLOAD_DIR,  # 다운로드 경로 지정
            "download.prompt_for_download": False,  # '다른 이름으로 저장' 대화상자 비활성화
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        chrome_options.add_experimental_option("prefs", prefs)

        if env == "production":
            print("운영 환경으로 판단하여 RDS에 직접 접속합니다.(Headless 모드)")

            # --- 서버 환경을 위한 옵션 추가 ---
            chrome_options.add_argument("--headless")  # GUI 없이 백그라운드에서 실행
            chrome_options.add_argument("--no-sandbox")  # Docker 컨테이너 환경에서 필수
            chrome_options.add_argument("--disable-dev-shm-usage")  # 공유 메모리 관련 문제 방지
            chrome_options.add_argument("--window-size=1920x1080")  # 창 크기 설정 (레이아웃 깨짐 방지)
            chrome_options.add_argument("--disable-gpu")  # <<< 개선 제안 2
            chrome_options.add_argument("--lang=ko_KR")  # <<< 개선 제안 2
            chrome_options.add_argument(
                "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36")  # 일반적인 사용자처럼 보이게 설정
        else:
            print("로컬 환경으로 드라이버 옵션을 설정합니다.")

        driver = webdriver.Chrome(options=chrome_options)

        if env != "production":
            driver.maximize_window()

        driver.set_page_load_timeout(60)
        url = "https://www.nongnet.or.kr/qlik/sso/single/?appid=551d7860-2a5d-49e5-915e-56517f3da2a3&sheet=d89143e2-368a-4d41-9851-d4f58ce060dc"
        wait = WebDriverWait(driver, 30)

        driver.get(url)
        print("▶ 웹사이트 접속 성공.")

        wait.until(EC.presence_of_element_located((By.XPATH, "//b[contains(text(), '시작일')]")))
        print("▶ 페이지 필터 로드 완료.")

        # 1단계: 날짜 선택
        select_date(driver, wait, "시작일", start_date)
        select_date(driver, wait, "종료일", end_date)

        # 2단계: 조회 조건 선택
        select_pummok(driver, wait, "배추")
        select_filter_option(driver, wait, "품종", "고냉지배추")
        select_filter_option(driver, wait, "거래단위", "10kg그물망", search_required=True)
        select_filter_option(driver, wait, "도매시장", "서울가락도매")
        select_filter_option(driver, wait, "산지-광역시도", "강원도")
        select_filter_option(driver, wait, "등급", "상")
        select_filter_option(driver, wait, "등급", "특")

        # 3단계: 조회 조건 적용을 위한 최종 [확인] 버튼 클릭
        print("\n▶ 모든 조건 적용을 위해 [확인] 버튼을 클릭합니다...")
        final_confirm_xpath = "//button[.//span[text()='확인']]"
        final_button = wait.until(EC.element_to_be_clickable((By.XPATH, final_confirm_xpath)))
        driver.execute_script("arguments[0].click();", final_button)

        print("▶ 데이터가 로드될 때까지 15초 대기합니다...")
        time.sleep(15)

        # ★★★ 4단계: 데이터 저장 버튼 클릭 ★★★
        print("\n▶ [데이터 저장] 버튼을 클릭하여 파일을 다운로드합니다...")
        download_button_id = "exportBtn"
        download_button = wait.until(EC.element_to_be_clickable((By.ID, download_button_id)))
        driver.execute_script("arguments[0].click();", download_button)
        print("\n🎉 모든 작업 완료! 파일 다운로드를 시작합니다.")

        # --- 파일 다운로드 완료 대기 로직 ---
        print(f"▶ '{DOWNLOAD_DIR}' 폴더에 파일이 생길 때까지 최대 60초 기다립니다...")
        seconds_waited = 0
        download_complete = False
        # 다운로드 전 폴더에 있던 파일 목록을 미리 가져옵니다.
        initial_files = set(os.listdir(DOWNLOAD_DIR))

        while seconds_waited < 60:
            # 현재 폴더의 파일 목록을 가져옵니다.
            current_files = set(os.listdir(DOWNLOAD_DIR))
            # 새로 생긴 파일이 있는지 확인합니다.
            new_files = current_files - initial_files

            # .crdownload (다운로드 중 임시 파일)이 아닌 파일이 생겼는지 확인
            for file in new_files:
                if not file.endswith(".crdownload"):
                    print(f"✅ 다운로드 완료: {file}")
                    download_complete = True
                    break

            if download_complete:
                break

            time.sleep(1)
            seconds_waited += 1

        if download_complete:
            is_success = True
        else:
            print("⚠️ 60초 내에 파일 다운로드가 완료되지 않았습니다.")
            is_success = False
        print("▶ 모든 작업이 완료되어 5초 후 브라우저를 종료합니다.")
        time.sleep(5)

    except Exception as e:
        print(f"\n스크립트 실행 중 오류가 발생하여 중단합니다: {e}")
        is_success = False
    finally:
        if 'driver' in locals() and driver.session_id:
            driver.quit()
            print("\n▶ 브라우저를 종료하고 스크립트를 마칩니다.")
        return is_success
