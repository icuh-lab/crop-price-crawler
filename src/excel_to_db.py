import os
import glob
import pandas as pd
from sqlalchemy import create_engine
import pymysql
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

# pymysql을 sqlalchemy가 인식할 수 있도록 설정
pymysql.install_as_MySQLdb()


def find_latest_excel_file(directory):
    """지정된 디렉토리에서 가장 최근에 수정된 엑셀(.xlsx) 파일을 찾습니다."""
    # 디렉토리 내의 모든 .xlsx 파일 경로를 리스트로 가져옵니다.
    list_of_files = glob.glob(os.path.join(directory, '*.xlsx'))
    if not list_of_files:
        return None
    # 수정 시간을 기준으로 가장 최신 파일을 찾습니다.
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def transform_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    다운로드한 엑셀의 데이터프레임을 DB 스키마에 맞게 변환합니다.
    - 한글 컬럼명을 영문으로 변경합니다.
    - 데이터 타입을 정리합니다 (숫자형, 날짜형).
    """
    print("\n▶ 데이터프레임 변환을 시작합니다...")

    # DB 스키마 순서에 맞는 영문 컬럼명 리스트 (id 제외)
    new_column_names = [
        'transaction_date',
        'transaction_unit',
        'average_price',
        'total_volume',
        'total_amount',
        'market_name',
        'corporation_name',
        'item_name',
        'item_variety',
        'origin_province',
        'origin_city',
        'grade'
    ]

    # 엑셀의 컬럼 개수와 DB 스키마의 컬럼 개수가 일치하는지 확인
    if len(df.columns) != len(new_column_names):
        raise ValueError(f"엑셀 컬럼 개수({len(df.columns)})와 DB 스키마 컬럼 개수({len(new_column_names)})가 일치하지 않습니다.")

    # 컬럼명 변경
    df.columns = new_column_names
    print("  - 컬럼명 영문으로 변경 완료.")

    # 데이터 타입 변환 및 정제
    # 1. 숫자형 컬럼에서 쉼표(,)를 제거하고 숫자로 변환
    numeric_cols = ['average_price', 'total_volume', 'total_amount']
    for col in numeric_cols:
        # pd.to_numeric에 errors='coerce'를 주면 숫자로 변환할 수 없는 값은 NaT(결측치)로 처리됩니다.
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

    # 2. 날짜 컬럼을 datetime 객체로 변환 (YYYY-MM-DD 형식)
    df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.date
    print("  - 데이터 타입 변환 완료 (숫자, 날짜).")

    print("▶ 데이터프레임 변환 완료.")
    return df


def insert_data(df: pd.DataFrame, table_name: str):
    """
    SSH 터널을 통해 데이터프레임을 지정된 테이블에 삽입합니다. (사용자 제공)
    """
    load_dotenv()

    env = os.getenv("EXECUTION_ENV", "local")
    print(f"--- 실행 환경: {env} ---")

    try:
        db_host = os.getenv("DB_HOST")
        db_port = int(os.getenv("DB_PORT"))
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_name = os.getenv("DB_NAME")

        if env == "production":
            print("운영 환경으로 판단하여 RDS에 직접 접속합니다.")

            conn_str = f'mysql+pymysql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'
            engine = create_engine(conn_str)

            print(f"\n▶ '{table_name}' 테이블에 데이터 삽입을 시작합니다...")
            df.to_sql(table_name, con=engine, if_exists='append', index=False)
            print(f"✅ 데이터 {len(df)}건이 성공적으로 삽입되었습니다.")
        else:
            print("로컬 환경으로 판단하여 SSH 터널링을 시작합니다.")
            ssh_host = os.getenv("SSH_HOST")
            ssh_port = int(os.getenv("SSH_PORT"))
            ssh_user = os.getenv("SSH_USER")
            ssh_pkey = os.getenv("SSH_PKEY")

            with SSHTunnelForwarder(
                    (ssh_host, ssh_port),
                    ssh_username=ssh_user,
                    ssh_pkey=ssh_pkey,
                    remote_bind_address=(db_host, db_port)
            ) as server:
                local_port = server.local_bind_port
                print(f"SSH 터널이 생성되었습니다. (localhost:{local_port} -> {db_host}:{db_port})")

                conn_str = f'mysql+pymysql://{db_user}:{db_password}@127.0.0.1:{local_port}/{db_name}'
                engine = create_engine(conn_str)

                print(f"\n▶ '{table_name}' 테이블에 데이터 삽입을 시작합니다...")
                df.to_sql(table_name, con=engine, if_exists='append', index=False)
                print(f"✅ 데이터 {len(df)}건이 성공적으로 삽입되었습니다.")
    except Exception as e:
        print(f"!! 오류: 데이터베이스 처리 중 문제가 발생했습니다: {e}")
        raise e


def main():
    """
    파서의 메인 실행 함수
    """
    print("--- 엑셀 파싱 및 DB 적재 작업을 시작합니다 ---")

    # --- 설정 ---
    TABLE_NAME = "drought_impact_crop_price_daily"

    # 프로젝트 루트 하위의 'output' 폴더 경로 설정
    # 현재 파일(excel_to_db.py)이 있는 디렉토리('src')를 찾습니다.
    src_directory = os.path.dirname(os.path.abspath(__file__))
    # 그 상위 디렉토리(프로젝트 루트)를 찾습니다.
    project_root = os.path.dirname(src_directory)
    # 프로젝트 루트 하위에 'output' 폴더 경로를 설정합니다.
    output_directory = os.path.join(project_root, "output")

    try:
        # 1. output 폴더에서 가장 최근 엑셀 파일 찾기
        latest_excel = find_latest_excel_file(output_directory)
        if latest_excel is None:
            print("!! output 폴더에 처리할 엑셀 파일이 없습니다.")
            return

        print(f"▶ 처리할 파일: {os.path.basename(latest_excel)}")

        # 2. 엑셀 파일을 데이터프레임으로 읽기
        df = pd.read_excel(latest_excel, header=0)

        # 3. 데이터프레임 변환 (컬럼명 변경, 데이터 타입 정제)
        transformed_df = transform_dataframe(df)

        print("\n▶ 변환된 데이터 샘플:")
        print(transformed_df.head())

        # 4. DB에 데이터 삽입 함수 호출
        insert_data(transformed_df, TABLE_NAME)

    except Exception as e:
        print(f"\n!! 최종 작업 실패: {e}")


if __name__ == '__main__':
    main()