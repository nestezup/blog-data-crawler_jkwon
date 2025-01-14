import streamlit as st
from app import NaverBlogCrawler
import io
import csv

def save_results_to_csv(results):
    # UTF-8-SIG 인코딩으로 BOM 추가
    output = io.StringIO()
    output.write('\ufeff')  # BOM 추가
    writer = csv.writer(output, quoting=csv.QUOTE_NONNUMERIC)  # 모든 필드를 따옴표로 감싸기
    
    # Write the header
    writer.writerow(['검색결과', '제목', '작성자', '작성일', '링크', '본문 내용'])
    
    # Write each result
    for idx, result in enumerate(results, 1):
        writer.writerow([
            f"검색결과 {idx}",
            result['title'],
            result['author'],
            result['date'],
            result['link'],
            result['content']
        ])
    
    return output.getvalue()

def main():
    st.title("네이버 블로그 크롤러")
    
    # 사이드바에 입력 폼 구성
    with st.sidebar:
        st.header("검색 설정")
        keyword = st.text_input("검색할 키워드를 입력하세요")
        post_count = st.number_input("수집할 포스트 개수", min_value=1, max_value=50, value=5)
        search_button = st.button("검색")
    
    # 메인 화면
    if search_button and keyword:
        with st.spinner('데이터를 수집하는 중입니다...'):
            crawler = NaverBlogCrawler()
            results = crawler.search_blogs(keyword, post_count=post_count)
            
            # 결과 표시
            for idx, result in enumerate(results, 1):
                with st.expander(f"검색결과 {idx}: {result['title']}"):
                    st.write(f"작성자: {result['author']}")
                    st.write(f"작성일: {result['date']}")
                    st.write(f"링크: {result['link']}")
                    st.write("본문 내용:")
                    st.text(result['content'])
            
            # Save results to CSV file
            csv_content = save_results_to_csv(results)
            st.download_button(
                label="결과를 CSV 파일로 다운로드",
                data=csv_content,
                file_name=f"naver_blog_search_{keyword}.csv",
                mime="text/csv",
            )
    
    elif search_button and not keyword:
        st.error("키워드를 입력해주세요!")

if __name__ == "__main__":
    main() 