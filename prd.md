## 네이버블로그 검색페이지에서 키워드로 검색을 하고, 
검색페이지의 url의 구조는 이렇게 생겼어.
https://search.naver.com/search.naver?ssc=tab.blog.all&sm=tab_jum&query=%EA%B2%A8%EC%9A%B8%EA%B5%AC%EB%91%90 



## 검색리스트에서 

### 제목 
<a href="https://blog.naver.com/hrelation/223671328400" class="title_link" data-cb-trigger="" data-cb-target="90000003_000000000000003413D99E90" onclick="return goOtherCR(this,'a=blg*f.nblg&amp;r=1&amp;i=90000003_000000000000003413D99E90&amp;u='+urlencode(this.href));" target="_blank"><mark>겨울</mark> 여아 <mark>구두</mark> 유아 메리제인 여자 아기 오즈키즈 털<mark>구두</mark></a>
여기에서 텍스트를 추출해야해. <mark>로 감싸져있는 부분도 전부 추출. 위의 예시에서는 "겨울 여아 구두 유아 메리제인 여자 아기 오즈키즈 털구두"를 추출해야해.

### 링크
- css selector인데, 
main_pack > section > div.api_subject_bx > ul > li:nth-child(1) > div > div.detail_box > div.title_area > a
여기에서 href의 속성값을 가져와야해.

### 작성자, 
#main_pack > section > div.api_subject_bx > ul > li:nth-child(1) > div > div.user_box > div.user_box_inner > div > a
의 innerText를 가져와야해.

### 작성일을 가져올 수 있어.
#main_pack > section > div.api_subject_bx > ul > li:nth-child(1) > div > div.user_box > div.user_box_inner > div > span
의 innerText를 가져와야해.

그리고, 본문의 내용은 위에서 수집한 url을 다시 리퀘스트해서 그 내용을 가져와야해..

## 링크를 request를 통해서 본문의 내용을 가져와야해. 
