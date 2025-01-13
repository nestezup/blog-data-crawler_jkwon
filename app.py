import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from io import StringIO
import chromedriver_autoinstaller
import subprocess

def setup_chrome_driver():
    # Chrome 설치 확인 및 설치
    try:
        subprocess.Popen(
            ['google-chrome', '--version'], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except:
        CHROME_INSTALL_CMD = """
        apt-get update
        apt-get install -y google-chrome-stable
        """
        subprocess.Popen(CHROME_INSTALL_CMD, shell=True)
    
    # ChromeDriver 자동 설치
    chromedriver_autoinstaller.install()
    
    # Chrome 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    return webdriver.Chrome(options=chrome_options)

def crawl_blog(keyword, num_posts):
    results = []
    log_container = st.empty()
    driver = setup_chrome_driver()
    
    try:
        # 네이버 접속
        log_container.write("네이버에 접속 중...")
        driver.get("https://www.naver.com")
        driver.maximize_window()
        
        # 검색어 입력
        log_container.write(f"검색어 '{keyword}' 입력 중...")
        search_box = driver.find_element(By.ID, "query")
        search_box.click()
        search_box.send_keys(keyword)
        search_box.send_keys(Keys.RETURN)
        
        # 블로그 탭 클릭
        log_container.write("블로그 탭으로 이동 중...")
        wait = WebDriverWait(driver, 10)
        blog_tab = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='tab.blog.all']")))
        blog_tab.click()
        time.sleep(3)
        
        # 블로그 링크 수집
        blog_links = driver.find_elements(By.CSS_SELECTOR, "a.title_link")
        log_container.write(f"총 {len(blog_links[:num_posts])}개의 블로그 포스트를 크롤링합니다...")
        
        for index, link in enumerate(blog_links[:num_posts], 1):
            blog_data = {
                "번호": index,
                "제목": link.text,
                "링크": link.get_attribute('href'),
                "본문": ""
            }
            
            # 티스토리 블로그인 경우 건너뛰기
            if "tistory.com" in blog_data['링크']:
                log_container.write(f"⚠️ [{index}/{num_posts}] 티스토리 블로그는 건너뜁니다: '{blog_data['제목']}'")
                continue
            
            log_container.write(f"[{index}/{num_posts}] '{blog_data['제목']}' 크롤링 중...")
            
            # 새 탭에서 블로그 열기
            driver.execute_script(f"window.open('{blog_data['링크']}', '_blank')")
            time.sleep(2)
            driver.switch_to.window(driver.window_handles[-1])
            
            try:
                if "post.naver.com" in blog_data['링크']:
                    log_container.write(f"네이버 포스트 처리 중... ({index}/{num_posts})")
                    content = get_naver_post_content(driver)
                else:
                    log_container.write(f"네이버 블로그 처리 중... ({index}/{num_posts})")
                    content = get_naver_blog_content(driver)
                    
                blog_data["본문"] = content
                log_container.write(f"✅ [{index}/{num_posts}] 완료!")
                results.append(blog_data)
                
            except Exception as e:
                error_msg = f"크롤링 실패: {str(e)}"
                blog_data["본문"] = error_msg
                log_container.write(f"❌ [{index}/{num_posts}] 실패: {error_msg}")
                results.append(blog_data)
            
            # 탭 닫기
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            time.sleep(1)
            
        log_container.write("✨ 크롤링이 완료되었습니다!")
            
    finally:
        driver.quit()
        
    return pd.DataFrame(results)

def get_naver_post_content(driver):
    # 네이버 포스트 크롤링 로직
    time.sleep(3)
    
    try:
        # 첫 번째 방법: 기존 구조
        content = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.se_component_wrap"))
        )
        return content.text.strip()
    except:
        try:
            # 두 번째 방법: 새로운 구조
            paragraphs = WebDriverWait(driver, 10).until(
                EC.presence_of_elements_located((By.CSS_SELECTOR, "div.se_component.se_paragraph.default"))
            )
            
            # 모든 문단의 텍스트를 결합
            texts = []
            for p in paragraphs:
                try:
                    # 일반 텍스트
                    text_element = p.find_element(By.CSS_SELECTOR, "p.se_textarea")
                    text = text_element.text.strip()
                    if text:
                        texts.append(text)
                except:
                    continue
            
            # 이미지 캡션도 포함
            try:
                captions = driver.find_elements(By.CSS_SELECTOR, "span.se_textarea")
                for caption in captions:
                    caption_text = caption.text.strip()
                    if caption_text:
                        texts.append(caption_text)
            except:
                pass
            
            return "\n".join(texts)
            
        except Exception as e:
            raise Exception(f"네이버 포스트 크롤링 실패: {str(e)}")

def get_naver_blog_content(driver):
    # 네이버 블로그 크롤링 로직
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe#mainFrame"))
    )
    driver.switch_to.frame(iframe)
    
    content = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "div.se-main-container"))
    )
    return content.text.strip()

# 메인 UI 부분 수정
st.set_page_config(
    page_title="네이버 블로그 크롤러",
    page_icon="🤖",
    layout="wide"
)

st.title("네이버 블로그 크롤러 🤖")

with st.expander("ℹ️ 사용 방법", expanded=True):
    st.markdown("""
    1. 검색어를 입력하세요
    2. 크롤링할 게시물 수를 선택하세요 (최대 20개)
    3. '크롤링 시작' 버튼을 클릭하세요
    4. 크롤링이 완료되면 결과를 CSV 파일로 다운로드할 수 있습니다
    
    ⚠️ **주의사항**
    - 크롤링은 시간이 걸릴 수 있습니다
    - 네트워크 상태에 따라 일부 게시물은 수집되지 않을 수 있습니다
    """)

# 사이드바에 입력 폼 배치
with st.sidebar:
    st.header("크롤링 설정")
    keyword = st.text_input("검색어를 입력하세요", "파이썬 selenium")
    num_posts = st.number_input("크롤링할 게시물 수", 
                               min_value=1, 
                               max_value=20, 
                               value=5,
                               help="한 번에 최대 20개까지 크롤링할 수 있습니다")
    
    start_crawl = st.button("크롤링 시작", 
                           help="버튼을 클릭하면 크롤링이 시작됩니다",
                           type="primary")

# 메인 화면
if start_crawl:
    try:
        with st.spinner(f"'{keyword}' 키워드로 {num_posts}개의 게시물을 크롤링하고 있습니다..."):
            df = crawl_blog(keyword, num_posts)
            
            if len(df) > 0:
                st.success("크롤링이 완료되었습니다! 🎉")
                
                # 결과 표시
                st.subheader("크롤링 결과")
                st.dataframe(df, use_container_width=True)
                
                # CSV 다운로드 버튼
                csv = df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSV 파일 다운로드",
                    data=csv,
                    file_name=f"blog_crawling_{keyword}.csv",
                    mime="text/csv",
                    help="크롤링 결과를 CSV 파일로 다운로드합니다"
                )
            else:
                st.warning("크롤링된 데이터가 없습니다. 다른 검색어로 시도해보세요.")
                
    except Exception as e:
        st.error(f"크롤링 중 오류가 발생했습니다: {str(e)}")
        st.info("잠시 후 다시 시도해주세요.") 