data "vault_kv_secret_v2" "hypervisor" {
  mount = "infra"
  name  = "dev/hypervisor"
}
data "vault_kv_secret_v2" "svc-init" {
  mount = "infra"
  name  = "dev/svc-init"
}
