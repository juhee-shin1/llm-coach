# OOMKilled 트러블슈팅

## 원인
컨테이너가 메모리 limits를 초과해서 커널이 강제 종료

## 진단 순서
1. `kubectl describe pod <pod>` 에서 OOMKilled 확인
2. `kubectl top pod <pod>` 로 메모리 사용량 확인

## 해결 방법
```bash
kubectl set resources deployment/<name> \
  --limits=memory=256Mi --requests=memory=128Mi
```

## 관련 태그
OOMKilled, resources, limits, requests
