# corpus — 소리 조각이 들어가는 곳

`corpus/default/` 는 처음 실행할 때 저절로 만들어집니다. 기본음의 배음으로 만든 사인파라
아무렇게나 겹쳐도 어울리고, 그만큼 심심합니다. 시작용입니다.

자기 소리로 바꾸는 것이 다음 단계입니다.

```bash
python make_corpus.py 내녹음.wav --name 첼로
python run.py --sim --corpus corpus/첼로
```

코퍼스 폴더는 저장소에 올라가지 않습니다(.gitignore). 녹음 파일은 각자 들고 있습니다.
