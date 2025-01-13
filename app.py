import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import quote
import re

class NaverBlogCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36'
        }
        
    def search_blogs(self, keyword, num_posts=1):
        """네이버 블로그 검색 및 데이터 수집"""
        results = []
        page = 1
        collected = 0
        
        while collected < num_posts:
            # 검색 URL 생성 (페이지네이션 포함)
            encoded_keyword = quote(keyword)
            search_url = f"https://search.naver.com/search.naver?where=blog&query={encoded_keyword}&start={1 + (page-1)*10}"
            
            # 검색 결과 페이지 가져오기
            response = requests.get(search_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 블로그 포스트 목록 추출
            blog_items = soup.select(".api_txt_lines.total_tit")
            if not blog_items:  # 더 이상 결과가 없으면 종료
                break
                
            for item in blog_items:
                if collected >= num_posts:
                    break
                    
                blog_data = {
                    "번호": collected + 1,
                    "제목": item.text.strip(),
                    "링크": item['href'],
                    "본문": "",
                    "작성자": "",
                    "작성일": ""
                }
                
                # 티스토리 블로그 건너뛰기
                if "tistory.com" in blog_data['링크']:
                    continue
                
                try:
                    # 작성자 정보 추출
                    writer_elem = item.find_parent().find_parent().select_one(".sub_txt.sub_name")
                    if writer_elem:
                        blog_data["작성자"] = writer_elem.text.strip()
                    
                    # 작성일 추출
                    date_elem = item.find_parent().find_parent().select_one(".sub_txt.sub_date")
                    if date_elem:
                        blog_data["작성일"] = date_elem.text.strip()
                    
                    # 본문 가져오기
                    if "post.naver.com" in blog_data['링크']:
                        content = self.get_naver_post_content(blog_data['링크'])
                    else:
                        content = self.get_naver_blog_content(blog_data['링크'])
                        
                    blog_data["본문"] = content
                    results.append(blog_data)
                    collected += 1
                    time.sleep(1)  # 요청 간격 조절
                    
                except Exception as e:
                    blog_data["본문"] = f"크롤링 실패: {str(e)}"
                    results.append(blog_data)
                    collected += 1
                    
            page += 1
            time.sleep(1)  # 페이지 요청 간격 조절
                    
        return pd.DataFrame(results)
    
    def get_naver_post_content(self, url):
        """네이버 포스트 본문 추출"""
        response = requests.get(url, headers=self.headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 본문 추출
        content_divs = soup.select("div.se_component.se_paragraph.default")
        texts = []
        
        for div in content_divs:
            text = div.get_text(strip=True)
            if text:
                texts.append(text)
                
        return "\n".join(texts)
    
    def get_naver_blog_content(self, url):
        """네이버 블로그 본문 추출"""
        try:
            # 실제 블로그 URL 추출
            if "blog.naver.com" in url:
                blog_id = re.search(r'blog.naver.com/([^?/]+)', url).group(1)
                log_no = re.search(r'logNo=(\d+)', url).group(1)
                url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
                
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # iframe 내부 컨텐츠 가져오기
            if "blog.naver.com" in url:
                iframe_url = soup.select_one("#mainFrame")['src']
                if not iframe_url.startswith('http'):
                    iframe_url = f"https://blog.naver.com{iframe_url}"
                response = requests.get(iframe_url, headers=self.headers)
                soup = BeautifulSoup(response.text, 'html.parser')
            
            # 여러 버전의 블로그 템플릿 지원
            content = None
            
            # 최신 버전 (se-main-container)
            content = soup.select_one("div.se-main-container")
            if content:
                return content.get_text(strip=True)
                
            # 구버전 (post-view)
            content = soup.select_one("div.post-view")
            if content:
                return content.get_text(strip=True)
                
            # 더 오래된 버전
            content = soup.select_one("div#postViewArea")
            if content:
                return content.get_text(strip=True)
                
            return "본문을 찾을 수 없습니다."
            
        except Exception as e:
            return f"본문 추출 실패: {str(e)}"

# Streamlit UI 설정
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
    keyword = st.text_input("검색어를 입력하세요", "파이썬 크롤링")
    num_posts = st.number_input(
        "크롤링할 게시물 수", 
        min_value=1, 
        max_value=20, 
        value=5,
        help="한 번에 최대 20개까지 크롤링할 수 있습니다"
    )
    
    start_crawl = st.button(
        "크롤링 시작", 
        help="버튼을 클릭하면 크롤링이 시작됩니다",
        type="primary"
    )

# 메인 화면
if start_crawl:
    try:
        with st.spinner(f"'{keyword}' 키워드로 {num_posts}개의 게시물을 크롤링하고 있습니다..."):
            crawler = NaverBlogCrawler()
            df = crawler.search_blogs(keyword, num_posts)
            
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