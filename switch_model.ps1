param([ValidateSet('Gemma','Qwen')][string]$Family)
$ErrorActionPreference = 'Stop'
$base = 'http://127.0.0.1:1234'
$models = @((Invoke-RestMethod "$base/api/v1/models").models | Where-Object { $_.type -eq 'llm' })
if ($models.Count -eq 0) { throw 'LM Studioでダウンロード済みのLLMが見つかりません。' }
for ($i=0; $i -lt $models.Count; $i++) { Write-Host "$($i+1). $($models[$i].display_name) [$($models[$i].key)]" }
if ($Family) {
    $matches = @($models | Where-Object { ($_.display_name + ' ' + $_.key) -match $Family })
    if ($matches.Count -ne 1) { throw 'モデル候補を一意に特定できません。-Familyを外して番号選択してください。' }
    $target = $matches[0]
} else {
    $answer = Read-Host 'ロードするモデル番号'
    $index = 0
    if (-not [int]::TryParse($answer,[ref]$index) -or $index -lt 1 -or $index -gt $models.Count) { throw '不正な番号です。' }
    $target = $models[$index-1]
}
Write-Host '重要: モデル切り替え前にworker.pyとapp.pyを停止してください。'
$confirm = Read-Host "'$($target.display_name)' に切り替えますか？ (yes)"
if ($confirm -ne 'yes') { Write-Host 'キャンセルしました'; exit 0 }
foreach ($model in $models) {
    foreach ($instance in @($model.loaded_instances)) {
        if ($null -eq $instance -or -not $instance.id) { continue }
        $payload = @{ instance_id = $instance.id } | ConvertTo-Json
        Invoke-RestMethod "$base/api/v1/models/unload" -Method Post -ContentType 'application/json' -Body $payload | Out-Null
    }
}
# API loading uses server-side default GPU offload. For explicit GPU offload use lms load --gpu.
$payload = @{ model=$target.key; context_length=2048; echo_load_config=$true } | ConvertTo-Json
$result = Invoke-RestMethod "$base/api/v1/models/load" -Method Post -ContentType 'application/json' -Body $payload
Write-Host "Loaded: $($target.display_name)"
Write-Host "Instance ID: $($result.instance_id)"
Write-Host 'Restart UI and worker. Leave LM_STUDIO_MODEL blank in .env for automatic single-loaded-model selection.'
