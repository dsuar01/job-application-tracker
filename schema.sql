CREATE DATABASE IF NOT EXISTS job_tracker;
USE job_tracker;

DROP TABLE IF EXISTS applications;
DROP TABLE IF EXISTS contacts;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS companies;

CREATE TABLE `companies` (
  `company_id` int(11) NOT NULL AUTO_INCREMENT,
  `company_name` varchar(100) NOT NULL,
  `industry` varchar(50) DEFAULT NULL,
  `website` varchar(200) DEFAULT NULL,
  `city` varchar(50) DEFAULT NULL,
  `state` varchar(50) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`company_id`),
  KEY `idx_company_industry` (`industry`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `jobs` (
  `job_id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `job_title` varchar(100) NOT NULL,
  `job_description` text,
  `salary_min` decimal(10,2) DEFAULT NULL,
  `salary_max` decimal(10,2) DEFAULT NULL,
  `job_type` varchar(20) DEFAULT NULL,
  `posting_url` varchar(500) DEFAULT NULL,
  `date_posted` date DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `requirements` json DEFAULT NULL,
  PRIMARY KEY (`job_id`),
  KEY `idx_company_type` (`company_id`,`job_type`),
  KEY `idx_job_title` (`job_title`),
  CONSTRAINT `jobs_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `applications` (
  `application_id` int(11) NOT NULL AUTO_INCREMENT,
  `job_id` int(11) NOT NULL,
  `application_date` date NOT NULL,
  `status` varchar(30) DEFAULT 'Applied',
  `resume_version` varchar(50) DEFAULT NULL,
  `cover_letter_sent` tinyint(1) DEFAULT '0',
  `response_date` date DEFAULT NULL,
  `interview_date` datetime DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `interview_data` json DEFAULT NULL,
  PRIMARY KEY (`application_id`),
  KEY `job_id` (`job_id`),
  KEY `idx_app_status` (`status`),
  CONSTRAINT `applications_ibfk_1` FOREIGN KEY (`job_id`) REFERENCES `jobs` (`job_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE `contacts` (
  `contact_id` int(11) NOT NULL AUTO_INCREMENT,
  `company_id` int(11) NOT NULL,
  `first_name` varchar(50) NOT NULL,
  `last_name` varchar(50) NOT NULL,
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `job_title` varchar(100) DEFAULT NULL,
  `linkedin_url` varchar(200) DEFAULT NULL,
  `notes` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`contact_id`),
  KEY `company_id` (`company_id`),
  CONSTRAINT `contacts_ibfk_1` FOREIGN KEY (`company_id`) REFERENCES `companies` (`company_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;