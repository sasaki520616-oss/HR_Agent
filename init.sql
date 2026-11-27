/*
 Navicat Premium Data Transfer

 Source Server         : employee_mgmt_db
 Source Server Type    : MySQL
 Source Server Version : 80038
 Source Host           : 127.0.0.1:3306
 Source Schema         : company_db

 Target Server Type    : MySQL
 Target Server Version : 80038
 File Encoding         : 65001

 Date: 27/11/2026 14:30:01
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for attendance
-- ----------------------------
DROP TABLE IF EXISTS `attendance`;
CREATE TABLE `attendance`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `employee_id` int(0) DEFAULT NULL,
  `work_date` date DEFAULT NULL,
  `check_in_time` datetime(0) DEFAULT NULL,
  `check_out_time` datetime(0) DEFAULT NULL,
  `status` enum('normal','late','early_leave','absent','leave') CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `late_minutes` int(0) DEFAULT NULL,
  `early_leave_minutes` int(0) DEFAULT NULL,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `employee_id`(`employee_id`) USING BTREE,
  CONSTRAINT `attendance_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 1474 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for attendance_history
-- ----------------------------
DROP TABLE IF EXISTS `attendance_history`;
CREATE TABLE `attendance_history`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `employee_id` int(0) DEFAULT NULL,
  `month_state` varchar(7) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `normal_days` int(0) DEFAULT 0,
  `late_count` int(0) DEFAULT 0,
  `early_leave_count` int(0) DEFAULT 0,
  `absent_days` int(0) DEFAULT 0,
  `leave_days` int(0) DEFAULT 0,
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `employee_id`(`employee_id`) USING BTREE,
  CONSTRAINT `attendance_history_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 514 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for change_requests
-- ----------------------------
DROP TABLE IF EXISTS `change_requests`;
CREATE TABLE `change_requests`  (
  `id` bigint(0) NOT NULL AUTO_INCREMENT,
  `action` varchar(64) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `old_data` json COMMENT '操作前的原数据快照，供审批核对与回退',
  `payload` json NOT NULL,
  `status` enum('PENDING','APPROVED','REJECTED','EXECUTED','FAILED') CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL DEFAULT 'PENDING',
  `requested_by` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `reason` varchar(255) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `idempotency_key` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `approved_by` varchar(128) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `created_at` datetime(0) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime(0) NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idempotency_key`(`idempotency_key`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 4 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for departments
-- ----------------------------
DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `dept_name` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `dept_code` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `manager_id` int(0) DEFAULT NULL,
  `parent_id` int(0) DEFAULT NULL,
  `created_at` timestamp(0) DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `dept_name`(`dept_name`) USING BTREE,
  UNIQUE INDEX `uk_dept_name`(`dept_name`) USING BTREE,
  UNIQUE INDEX `dept_code`(`dept_code`) USING BTREE,
  INDEX `fk_dept_parent`(`parent_id`) USING BTREE,
  CONSTRAINT `fk_dept_parent` FOREIGN KEY (`parent_id`) REFERENCES `departments` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 8 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for employees
-- ----------------------------
DROP TABLE IF EXISTS `employees`;
CREATE TABLE `employees`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `employee_no` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `name` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `gender` enum('M','F') CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `birth_date` date DEFAULT NULL,
  `hire_date` date DEFAULT NULL,
  `position_id` int(0) DEFAULT NULL,
  `phone` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `email` varchar(100) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `department_id` int(0) DEFAULT NULL,
  `manager_id` int(0) DEFAULT NULL,
  `status` enum('active','inactive','resigned') CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT 'active',
  `created_at` timestamp(0) DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp(0) DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP(0),
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `employee_no`(`employee_no`) USING BTREE,
  UNIQUE INDEX `uk_emp_no`(`employee_no`) USING BTREE,
  UNIQUE INDEX `uk_emp_phone`(`phone`) USING BTREE,
  UNIQUE INDEX `uk_emp_email`(`email`) USING BTREE,
  INDEX `fk_emp_dept`(`department_id`) USING BTREE,
  INDEX `fk_emp_pos`(`position_id`) USING BTREE,
  INDEX `fk_emp_manager`(`manager_id`) USING BTREE,
  INDEX `idx_emp_name`(`name`) USING BTREE,
  CONSTRAINT `fk_emp_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT,
  CONSTRAINT `fk_emp_manager` FOREIGN KEY (`manager_id`) REFERENCES `employees` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT,
  CONSTRAINT `fk_emp_pos` FOREIGN KEY (`position_id`) REFERENCES `positions` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT
) ENGINE = InnoDB AUTO_INCREMENT = 100050 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_bin ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for positions
-- ----------------------------
DROP TABLE IF EXISTS `positions`;
CREATE TABLE `positions`  (
  `id` int(0) NOT NULL AUTO_INCREMENT,
  `title` varchar(50) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin NOT NULL,
  `level` varchar(20) CHARACTER SET utf8mb3 COLLATE utf8mb3_bin DEFAULT NULL,
  `description` text CHARACTER SET utf8mb3 COLLATE utf8mb3_bin,
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `title`(`title`) USING BTREE,
  UNIQUE INDEX `uk_pos_title`(`title`) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 13 CHARACTER SET = utf8mb3 COLLATE = utf8mb3_bin ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;
