variable "name" {}
variable "lambda_arns" {
  type = list(string)
}

resource "aws_api_gateway_rest_api" "this" {
  name = var.name
}

resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.this.id
  http_method = aws_api_gateway_method.this.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = element(var.lambda_arns, 0)
}