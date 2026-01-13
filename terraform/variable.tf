# variables.tf
variable "environment" {
  description = "배포 환경 (dev 또는 prod)"
  type        = string
}

variable "cpu" {
  description = "Fargate CPU (dev는 작게, prod는 크게)"
  default     = 256
}

variable "memory" {
  description = "Fargate Memory"
  default     = 512
}

variable "desired_count" {
  description = "실행할 컨테이너 개수"
  default     = 1
}

# variables.tf (기존 내용 아래에 추가)

variable "vpc_id" {
  description = "사용할 VPC ID (직접 입력)"
  type        = string
}

variable "subnet_ids" {
  description = "사용할 Subnet ID 목록 (2개 이상)"
  type        = list(string)
}
