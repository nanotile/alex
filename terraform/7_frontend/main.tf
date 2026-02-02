# Aurora Serverless v2 Cluster
resource "aws_rds_cluster" "aurora" {
  cluster_identifier     = "alex-aurora-cluster"
  engine                 = "aurora-postgresql"
  engine_mode            = "provisioned"
  engine_version         = "15.12"
  database_name          = "alex"
  master_username        = "alexadmin"
  master_password        = random_password.db_password.result
  
  # Serverless v2 scaling configuration
  serverlessv2_scaling_configuration {
    min_capacity = var.min_capacity
    max_capacity = var.max_capacity
  }
  
  # Enable Data API
  enable_http_endpoint = true
  
  # Networking
  db_subnet_group_name   = aws_db_subnet_group.aurora.name
  vpc_security_group_ids = [aws_security_group.aurora.id]
  
  # Backup and maintenance
  backup_retention_period   = 7
  preferred_backup_window   = "03:00-04:00"
  preferred_maintenance_window = "sun:04:00-sun:05:00"
  
  # --- UPDATED FOR COST MINIMIZATION ---
  # Replaces hardcoded 'true' with a variable for external control 
  skip_final_snapshot = var.skip_final_snapshot 
  
  # Ensure deletion protection is disabled to allow automated destruction
  deletion_protection = false 
  # -------------------------------------

  apply_immediately   = true
  
  tags = {
    Project = "alex"
    Part    = "5"
  }
}