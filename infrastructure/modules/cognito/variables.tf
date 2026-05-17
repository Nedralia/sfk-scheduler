variable "user_pool_name" {
  description = "Name of the Cognito User Pool."
  type        = string
}

variable "domain_prefix" {
  description = "Cognito hosted-UI domain prefix (must be globally unique across all AWS accounts)."
  type        = string
}

variable "callback_urls" {
  description = "Allowed OAuth 2.0 callback (redirect) URLs for the web app client."
  type        = list(string)
}

variable "logout_urls" {
  description = "Allowed OAuth 2.0 logout URLs for the web app client."
  type        = list(string)
}

variable "mfa_configuration" {
  description = "MFA enforcement level: OFF, OPTIONAL, or ON."
  type        = string
  default     = "OPTIONAL"

  validation {
    condition     = contains(["OFF", "OPTIONAL", "ON"], var.mfa_configuration)
    error_message = "mfa_configuration must be one of: OFF, OPTIONAL, ON."
  }
}

variable "password_min_length" {
  description = "Minimum password length."
  type        = number
  default     = 12
}

variable "advanced_security_mode" {
  description = "Cognito advanced security mode: OFF, AUDIT, or ENFORCED."
  type        = string
  default     = "ENFORCED"

  validation {
    condition     = contains(["OFF", "AUDIT", "ENFORCED"], var.advanced_security_mode)
    error_message = "advanced_security_mode must be one of: OFF, AUDIT, ENFORCED."
  }
}

variable "access_token_validity" {
  description = "Access token validity in hours."
  type        = number
  default     = 1
}

variable "id_token_validity" {
  description = "ID token validity in hours."
  type        = number
  default     = 1
}

variable "refresh_token_validity" {
  description = "Refresh token validity in days."
  type        = number
  default     = 30
}

variable "tags" {
  description = "Tags to apply to all resources."
  type        = map(string)
  default     = {}
}
