output "user_pool_id" {
  description = "ID of the Cognito User Pool."
  value       = aws_cognito_user_pool.this.id
}

output "user_pool_arn" {
  description = "ARN of the Cognito User Pool."
  value       = aws_cognito_user_pool.this.arn
}

output "user_pool_endpoint" {
  description = "Endpoint of the Cognito User Pool (used as the OIDC issuer base URL)."
  value       = aws_cognito_user_pool.this.endpoint
}

output "web_client_id" {
  description = "ID of the Cognito User Pool web app client."
  value       = aws_cognito_user_pool_client.web.id
}

output "hosted_ui_domain" {
  description = "Base URL of the Cognito hosted-UI."
  value       = "https://${aws_cognito_user_pool_domain.this.domain}.auth.${data.aws_region.current.name}.amazoncognito.com"
}
