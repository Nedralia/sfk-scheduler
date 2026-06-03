# SFK Landing Page

Vue + TypeScript landing page for visualizing the cleaning schedule from `/data/schedule`.

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
npm run preview
```

The app reads schedule data from `/schedule` first, then `/schedule.csv`.

## Deploy

```bash
npm run deploy
```

This calls `deploy.sh`, which syncs the built `dist/` to S3 and invalidates the CloudFront cache. The script requires two environment variables:

| Variable | Description |
|---|---|
| `BUCKET_NAME` | S3 bucket that hosts the website (e.g. `sfk-scheduler-web-992382661713-eu-north-1`) |
| `DISTRIBUTION_ID` | CloudFront distribution ID (e.g. `EBDGRJ1SFCCH0`) |

## CI/CD

A GitHub Actions workflow (`.github/workflows/deploy-page.yml`) automatically builds and deploys the page on every push to `main` that touches files under `src/page/**`.

### Required repository secrets

Before the workflow can run, the following secrets must be added to the repository at **Settings → Secrets and variables → Actions**:

| Secret | Description |
|---|---|
| `AWS_ACCESS_KEY_ID` | AWS IAM access key with S3 write and CloudFront invalidation permissions |
| `AWS_SECRET_ACCESS_KEY` | Corresponding AWS secret access key |
| `WEBSITE_BUCKET_NAME` | S3 bucket name that hosts the website |
| `CLOUDFRONT_DISTRIBUTION_ID` | CloudFront distribution ID serving the website |

### IAM permissions required

The IAM user or role behind the credentials needs at minimum:

```json
{
  "Effect": "Allow",
  "Action": ["s3:PutObject", "s3:DeleteObject", "s3:ListBucket"],
  "Resource": ["arn:aws:s3:::BUCKET_NAME", "arn:aws:s3:::BUCKET_NAME/*"]
},
{
  "Effect": "Allow",
  "Action": "cloudfront:CreateInvalidation",
  "Resource": "arn:aws:cloudfront::ACCOUNT_ID:distribution/DISTRIBUTION_ID"
}
```
