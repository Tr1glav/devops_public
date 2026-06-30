sudo apt install python3.12-venv

python3.12 -m venv ~/venv

source ~/venv/bin/activate

pip install -r ./requirement.txt

deactivate

source ~/venv/bin/activate

va (){
  eval `ssh-agent -s`
  source ~/venv/bin/activate

  export VAULT_ADDR="https://vault.dev.dla.su"
  export VAULT_TOKEN=<hidden>
  export TF_VAR_vault_addr=`printenv 'VAULT_ADDR'`
  export TF_VAR_vault_token=`printenv 'VAULT_TOKEN'`
  
  SSH_PASSPHRASE=$(vault kv get -field=key_password infra/dev/svc-init) || {
    echo "ERROR: Failed to get SSH passphrase from Vault"
    return 1
  }

  expect <<EOF
    spawn ssh-add /home/user/.ssh/svc-init
    expect "passphrase"
    send "$SSH_PASSPHRASE\r"
    expect eof
EOF
}

ansible-galaxy install 'git+https://github.com/TerryHowe/ansible-modules-hashivault.git'

kubespray

cd /

git submodule update

cd /kubespray

pip3 install -r requirements.txt
