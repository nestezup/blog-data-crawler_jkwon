import requests
from bs4 import BeautifulSoup
from urllib.parse import quote

class NaverBlogCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

    def search_blogs(self, keyword, post_count=10):
        results = []
        encoded_keyword = quote(keyword)
        url = f'https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query={encoded_keyword}'
        
        try:
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            blog_lists = soup.select('div.api_subject_bx ul > li')
            
            # post_count만큼만 처리
            for blog in blog_lists[:post_count]:
                try:
                    # 제목 추출 (mark 태그 포함하여 추출)
                    title_element = blog.select_one('div.detail_box > div.title_area > a')
                    title = ''.join(title_element.stripped_strings) if title_element else ''
                    
                    # 링크 추출
                    link = title_element.get('href') if title_element else ''
                    
                    # 작성자 추출
                    author_element = blog.select_one('div.user_box > div.user_box_inner > div > a')
                    author = author_element.text.strip() if author_element else ''
                    
                    # 작성일 추출
                    date_element = blog.select_one('div.user_box > div.user_box_inner > div > span')
                    date = date_element.text.strip() if date_element else ''
                    
                    # 블로그 본문 내용 가져오기
                    content = self.get_blog_content(link) if link else ''
                    
                    blog_data = {
                        'title': title,
                        'link': link,
                        'author': author,
                        'date': date,
                        'content': content
                    }
                    
                    results.append(blog_data)
                    
                except Exception as e:
                    print(f"Error processing blog entry: {e}")
                    
        except Exception as e:
            print(f"Error fetching page: {e}")
            
        return results

    def get_blog_content(self, url):
        try:
            # 블로그 URL을 모바일 버전으로 변경
            if 'blog.naver.com' in url:
                url = url.replace('blog.naver.com', 'm.blog.naver.com')
            
            response = requests.get(url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            if 'm.blog.naver.com' in url:
                # 수정된 선택자로 본문 컨테이너 찾기
                main_container = soup.select_one('#viewTypeSelector > div > div > div.se-main-container')
                if main_container:
                    # se-text 클래스를 가진 모든 요소 찾기
                    text_blocks = []
                    text_elements = main_container.find_all(class_='se-text')
                    
                    for element in text_elements:
                        # 각 se-text 요소 내의 모든 텍스트 노드 수집
                        all_texts = []
                        for text in element.stripped_strings:
                            if text.strip():
                                all_texts.append(text.strip())
                        if all_texts:
                            text_blocks.append(' '.join(all_texts))
                    
                    # 모든 텍스트 블록을 줄바꿈으로 연결
                    content = '\n'.join(text_blocks)
                    return content
                    
                # 구 버전 에디터용 대체 선택자 추가
                old_container = soup.select_one('.post-view')
                if old_container:
                    text_elements = old_container.find_all(['p', 'span'])
                    content = '\n'.join([elem.get_text(strip=True) for elem in text_elements if elem.get_text(strip=True)])
                    return content
            
            return ''
            
        except Exception as e:
            print(f"Error fetching blog content: {e}")
            return ''

def main():
    crawler = NaverBlogCrawler()
    results = crawler.search_blogs('청바지', post_count=10)
    
    for idx, result in enumerate(results, 1):
        print(f"\n=== 검색결과 {idx} ===")
        print(f"제목: {result['title']}")
        print(f"작성자: {result['author']}")
        print(f"작성일: {result['date']}")
        print(f"링크: {result['link']}")
        print(f"본문 미리보기: {result['content']}")

if __name__ == "__main__":
    main() 