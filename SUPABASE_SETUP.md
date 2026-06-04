# Supabase 연결 방법

1. Supabase 프로젝트를 만든 뒤 SQL Editor에서 [supabase-schema.sql](</Users/GA/Documents/New project/apex 테스트/supabase-schema.sql>) 내용을 실행합니다.
2. Supabase 대시보드 `Settings > API` 에서 아래 2개 값을 확인합니다.
   `Project URL`
   `anon public key`
3. 값을 [supabase-config.js](</Users/GA/Documents/New project/apex 테스트/supabase-config.js>) 에 넣습니다.
4. 페이지에서 테스트를 끝내면 결과가 `apex_test_results` 테이블에 자동 저장됩니다.

저장되는 주요 데이터:

- 총점, 퍼센타일, 단계명
- 강점 영역, 약점 영역
- Part 1~4 점수
- Part 7 분류 결과, Part 8 초단문 프롬프트 원문
- 세부 서브스코어
- 접속 URL, user agent, 클라이언트 생성 시각

주의:

- `anon key`는 공개 클라이언트용 키라 정적 페이지에 넣을 수 있습니다.
- 대신 RLS는 `insert만 허용`하고 `select는 차단`하도록 [supabase-schema.sql](</Users/GA/Documents/New project/apex 테스트/supabase-schema.sql>) 에 설정되어 있습니다.
- 현재 구조는 `시험 결과 기록`용입니다. 이름, 이메일, 회사명까지 수집하려면 별도 입력 폼과 테이블 컬럼을 추가해야 합니다.
