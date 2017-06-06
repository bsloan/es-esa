resource "aws_elasticsearch_domain" "es" {
  domain_name           = "es-esa"
  elasticsearch_version = "2.3"

  cluster_config {
    instance_type = "t2.micro.elasticsearch"
  }

  ebs_options {
    ebs_enabled = true
    volume_size = 30
    volume_type = "gp2"
  }

  advanced_options {
    "rest.action.multi.allow_explicit_index" = "true"
  }

  access_policies = <<CONFIG
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "AWS": "arn:aws:iam::892100926213:role/EC2-Elasticsearch-User"
            },
        "Action": "es:*",
        "Resource": "arn:aws:es:us-east-1:892100926213:domain/es-esa/*"
        }
    ]
}
CONFIG

  snapshot_options {
    automated_snapshot_start_hour = 23
  }

  tags {
    Domain = "ESADomain"
  }
}