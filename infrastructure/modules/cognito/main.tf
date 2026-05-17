data "aws_region" "current" {}

resource "aws_cognito_user_pool" "this" {
  name = var.user_pool_name

  # Sign-in via email address
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length                   = var.password_min_length
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  # MFA (TOTP software token)
  mfa_configuration = var.mfa_configuration

  software_token_mfa_configuration {
    enabled = var.mfa_configuration != "OFF"
  }

  # Self-service account recovery via verified email
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Email verification code
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
  }

  # Email schema attribute (required)
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true

    string_attribute_constraints {
      min_length = 5
      max_length = 254
    }
  }

  # Advanced security (adaptive authentication, compromised credentials)
  user_pool_add_ons {
    advanced_security_mode = var.advanced_security_mode
  }

  tags = var.tags
}

# Public SPA client — authorization code flow with PKCE, no client secret.
# Cognito enforces PKCE for public clients (generate_secret = false) by
# requiring code_challenge / code_challenge_method in the authorization request.
resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.user_pool_name}-web-client"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = false

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["openid", "email", "profile"]

  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  supported_identity_providers = ["COGNITO"]

  access_token_validity  = var.access_token_validity
  id_token_validity      = var.id_token_validity
  refresh_token_validity = var.refresh_token_validity

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # Prevent user-existence enumeration attacks
  prevent_user_existence_errors = "ENABLED"

  # Intentionally browser-only auth flows: SRP for sign-in and token refresh.
  # ALLOW_USER_PASSWORD_AUTH is omitted to prevent plaintext password flows
  # that would expose credentials to the SDK/CLI transport layer.
  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]
}

# Cognito hosted-UI domain (prefix must be globally unique)
resource "aws_cognito_user_pool_domain" "this" {
  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}
