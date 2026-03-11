# ImagePullBackOff / ErrImagePull 트러블슈팅

## 원인
- 존재하지 않는 이미지 태그
- Private registry 인증 실패
- 네트워크 문제

## 진단 순서
1. `kubectl get pods -n <namespace>` 로 상태 확인
2. `kubectl describe pod <pod> -n <namespace>` 로 Events 확인
3. Events에서 Failed to pull image 메시지 확인

## 해결 방법
### 이미지 태그 오타인 경우
```bash
kubectl set image deployment/<name> <container>=<image>:<correct-tag> -n <namespace>
kubectl rollout status deployment/<name> -n <namespace>
```

## 관련 태그
CrashLoopBackOff, ImagePullBackOff, ErrImagePull, Deployment
