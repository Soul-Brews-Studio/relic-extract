01-scan.md:73 | severe | "รอบถัดมาเล็กลงเรื่อย ๆ" but round 1 new 178,147 is bigger than round 0 87,788 | capture 03:9-10 | say round 1 jumps (copies), then it shrinks from round 2/3
01-scan.md:78 | severe | "รอบ 4 ถึง 7 new ค้างที่ 5,309 ทุกรอบ" but round 4 shows new 5,311 (grown 4, rewritten 14) | capture 03:6 | say "รอบ 5 ถึง 7" 
01-scan.md:99 | severe | unreadable.json said to match the 1,046 folders; capture 04 shows only the file name, not its content; meta/ also has 5 more entries not listed | capture 04:24-33 | drop "ตรงกับ 1,046" or show a count
01-scan.md:110 | minor | the bash block "duckdb: rows by what they are" is a label, not a runnable command; the SQL is never shown, yet the foreword says every command was run | capture 05:1 | show the real SQL or mark as label
01-scan.md:73-74 | minor | reason for 178,147 new ("เพราะมี copies กับไฟล์ที่ past เปลี่ยน") is inference; capture only shows copies 68,583, past 28, which do not sum to it | capture 03:9 | soften to "ในนั้นมี copies 68,583"
01-scan.md:22 | minor | groups `up` as a view command, but help says up runs `run` first and then serves | capture 01:11 | move `up` out of the view group
01-scan.md:13 | minor | "run ใช้จริงทุกวัน" is a habit claim; help shows only that run is incremental | capture 01:10 | cut "ทุกวัน" or cite the log
00-foreword.md:24 | minor | says images have three sources, but D1-chain/D2-broke diagrams are neither terminal capture, page screenshot, nor cover | capture - | add a fourth source: diagrams
00-foreword.md:22 | minor | "ผม" in the foreword, while the rest of the book and line 38 say the author is relic-extract (an AI), no pronoun elsewhere | - | use "เล่มนี้" or keep one voice
