# PVC 마운트 실패 트러블슈팅

## 원인
- PVC가 없거나 Pending 상태
- StorageClass 없음
- 다른 노드에 이미 마운트됨 (RWO)

## 진단 순서
1. `kubectl get pvc -n <namespace>`
2. `kubectl describe pvc <name> -n <namespace>`
3. `kubectl get storageclass`

## 관련 태그
PVC, PersistentVolume, StorageClass, Pending
