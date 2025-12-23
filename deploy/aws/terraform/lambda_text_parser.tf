data "archive_file" "text_parser_zip" {
  type        = "zip"
  source_dir  = "${path.module}/../../../lambda/text_parser"
  output_path = "${path.module}/.terraform/text-parser.zip"
}

data "aws_iam_role" "text_parser" {
  name = var.lambda_text_parser_role_name
}

resource "aws_lambda_function" "text_parser" {
  function_name = var.lambda_text_parser_name
  role          = data.aws_iam_role.text_parser.arn
  handler       = var.lambda_text_parser_handler
  runtime       = var.lambda_text_parser_runtime
  filename      = data.archive_file.text_parser_zip.output_path
  memory_size   = var.lambda_text_parser_memory
  timeout       = var.lambda_text_parser_timeout

  environment {
    variables = var.lambda_text_parser_env
  }
}

resource "aws_iam_role_policy" "text_parser_bedrock" {
  count = var.enable_bedrock_policy ? 1 : 0
  name  = "${var.lambda_text_parser_name}-bedrock"
  role  = data.aws_iam_role.text_parser.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"]
        Effect   = "Allow"
        Resource = var.bedrock_model_arns
      }
    ]
  })
}

resource "aws_apigatewayv2_api" "text_parser" {
  count         = var.enable_text_parser_api ? 1 : 0
  name          = "${var.lambda_text_parser_name}-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "text_parser" {
  count                = var.enable_text_parser_api ? 1 : 0
  api_id               = aws_apigatewayv2_api.text_parser[0].id
  integration_type     = "AWS_PROXY"
  integration_uri      = aws_lambda_function.text_parser.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "text_parser" {
  count     = var.enable_text_parser_api ? 1 : 0
  api_id    = aws_apigatewayv2_api.text_parser[0].id
  route_key = "POST /parse"
  target    = "integrations/${aws_apigatewayv2_integration.text_parser[0].id}"
}

resource "aws_apigatewayv2_stage" "text_parser" {
  count       = var.enable_text_parser_api ? 1 : 0
  api_id      = aws_apigatewayv2_api.text_parser[0].id
  name        = "$default"
  auto_deploy = true
}

resource "aws_lambda_permission" "text_parser_api" {
  count         = var.enable_text_parser_api ? 1 : 0
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.text_parser.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.text_parser[0].execution_arn}/*/*"
}
