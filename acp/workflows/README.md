# ACP Workflows

| Workflow | File | Status |
|----------|------|--------|
| Resume parse | [resume-parse.yaml](./resume-parse.yaml) | ✅ implemented |
| Job discovery | [job-discovery.yaml](./job-discovery.yaml) | 🟡 agent partial |
| Tailor resume | [tailor-resume.yaml](./tailor-resume.yaml) | 🟡 API exists |
| Apply job | [apply-job.yaml](./apply-job.yaml) | 🔴 planned |

## Runtime mapping

YAML here is the **contract**. Python handlers live under:

`apps/api/src/careerpilot/acp/workflows/`
