environment   = "dev"
cpu           = 256
memory        = 512
desired_count = 1
vpc_id        = "vpc-c90384a2"
subnet_ids = [
  "subnet-b311e7ec",
  "subnet-58d06033",
  "subnet-d590749a",
  "subnet-28d6b453"
]
acm_certificate_arn = "arn:aws:acm:ap-northeast-2:554522139279:certificate/0d440dff-e381-4607-98d3-eb6e02737149"
