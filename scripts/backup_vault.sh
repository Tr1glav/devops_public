curl \
  --header "X-Vault-Token: $VAULT_TOKEN" \
  --request POST \
  https://vault.dev.dla.su/v1/sys/storage/raft/snapshot \
  -o vault.snapshot