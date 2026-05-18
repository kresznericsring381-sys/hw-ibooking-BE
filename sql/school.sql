-- MySQL dump 10.13  Distrib 8.0.28, for Win64 (x86_64)
--
-- Host: localhost    Database: school
-- ------------------------------------------------------
-- Server version	8.0.28

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `orders`
--

DROP TABLE IF EXISTS `orders`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `orders` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '订单ID',
  `student_id` varchar(20) NOT NULL COMMENT '学生学号',
  `seat_id` int NOT NULL COMMENT '座位ID',
  `start_time` datetime NOT NULL COMMENT '开始时间',
  `end_time` datetime NOT NULL COMMENT '结束时间',
  `status` tinyint DEFAULT '0' COMMENT '状态：0=待签到，1=使用中，2=已完成，3=违约，4=已取消',
  `sign_time` datetime DEFAULT NULL COMMENT '签到时间',
  `finish_time` datetime DEFAULT NULL COMMENT '结束时间',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_student` (`student_id`),
  KEY `idx_seat` (`seat_id`),
  CONSTRAINT `fk_order_seat` FOREIGN KEY (`seat_id`) REFERENCES `seat` (`id`) ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `fk_order_student` FOREIGN KEY (`student_id`) REFERENCES `student` (`student_id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='自习预约订单表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orders`
--

LOCK TABLES `orders` WRITE;
/*!40000 ALTER TABLE `orders` DISABLE KEYS */;
INSERT INTO `orders` VALUES (1,'2026001',1,'2026-05-06 09:00:00','2026-05-06 11:00:00',4,'2026-05-06 09:05:00',NULL,'2026-05-06 10:29:09'),(2,'2026002',2,'2026-05-06 14:00:00','2026-05-06 16:00:00',3,NULL,NULL,'2026-05-06 10:29:09'),(3,'2026003',3,'2026-05-05 19:00:00','2026-05-05 21:00:00',2,'2026-05-05 19:02:00','2026-05-05 21:00:00','2026-05-06 10:29:09');
/*!40000 ALTER TABLE `orders` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `room`
--

DROP TABLE IF EXISTS `room`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `room` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '教室ID',
  `name` varchar(50) NOT NULL COMMENT '教室名称',
  `open_time` time NOT NULL COMMENT '开放时间',
  `close_time` time NOT NULL COMMENT '关闭时间',
  `status` tinyint DEFAULT '1' COMMENT '状态：0=停用，1=正常',
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='教室信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `room`
--

LOCK TABLES `room` WRITE;
/*!40000 ALTER TABLE `room` DISABLE KEYS */;
INSERT INTO `room` VALUES (1,'一号自习室','08:00:00','22:00:00',1),(2,'二号自习室','08:00:00','23:00:00',1);
/*!40000 ALTER TABLE `room` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `seat`
--

DROP TABLE IF EXISTS `seat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `seat` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '座位ID',
  `room_id` int NOT NULL COMMENT '所属教室ID',
  `x` int NOT NULL COMMENT '行坐标',
  `y` int NOT NULL COMMENT '列坐标',
  `status` tinyint DEFAULT '0' COMMENT '状态：0=空闲，1=占用',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_seat_room_xy` (`room_id`,`x`,`y`),
  KEY `idx_room` (`room_id`),
  CONSTRAINT `fk_seat_room` FOREIGN KEY (`room_id`) REFERENCES `room` (`id`) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=107 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='座位信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `seat`
--

LOCK TABLES `seat` WRITE;
/*!40000 ALTER TABLE `seat` DISABLE KEYS */;
INSERT INTO `seat` VALUES (1,1,1,1,0),(2,1,1,2,0),(3,1,1,3,0),(4,1,2,1,0),(5,1,2,2,0),(6,1,2,3,0),(7,2,0,0,1),(8,2,0,1,1),(9,2,0,2,1),(10,2,0,3,1),(11,2,0,4,1),(12,2,0,5,1),(13,2,0,6,1),(14,2,0,7,1),(15,2,0,8,1),(16,2,0,9,1),(17,2,1,0,1),(18,2,1,1,1),(19,2,1,2,1),(20,2,1,3,1),(21,2,1,4,1),(22,2,1,5,1),(23,2,1,6,1),(24,2,1,7,1),(25,2,1,8,1),(26,2,1,9,1),(27,2,2,0,1),(28,2,2,1,1),(29,2,2,2,1),(30,2,2,3,1),(31,2,2,4,1),(32,2,2,5,1),(33,2,2,6,1),(34,2,2,7,1),(35,2,2,8,1),(36,2,2,9,1),(37,2,3,0,1),(38,2,3,1,1),(39,2,3,2,1),(40,2,3,3,1),(41,2,3,4,1),(42,2,3,5,1),(43,2,3,6,1),(44,2,3,7,1),(45,2,3,8,1),(46,2,3,9,1),(47,2,4,0,1),(48,2,4,1,1),(49,2,4,2,1),(50,2,4,3,1),(51,2,4,4,1),(52,2,4,5,1),(53,2,4,6,1),(54,2,4,7,1),(55,2,4,8,1),(56,2,4,9,1),(57,2,5,0,1),(58,2,5,1,1),(59,2,5,2,1),(60,2,5,3,1),(61,2,5,4,1),(62,2,5,5,1),(63,2,5,6,1),(64,2,5,7,1),(65,2,5,8,1),(66,2,5,9,1),(67,2,6,0,1),(68,2,6,1,1),(69,2,6,2,1),(70,2,6,3,1),(71,2,6,4,1),(72,2,6,5,1),(73,2,6,6,1),(74,2,6,7,1),(75,2,6,8,1),(76,2,6,9,1),(77,2,7,0,1),(78,2,7,1,1),(79,2,7,2,1),(80,2,7,3,1),(81,2,7,4,1),(82,2,7,5,1),(83,2,7,6,1),(84,2,7,7,1),(85,2,7,8,1),(86,2,7,9,1),(87,2,8,0,1),(88,2,8,1,1),(89,2,8,2,1),(90,2,8,3,1),(91,2,8,4,1),(92,2,8,5,1),(93,2,8,6,1),(94,2,8,7,1),(95,2,8,8,1),(96,2,8,9,1),(97,2,9,0,1),(98,2,9,1,1),(99,2,9,2,1),(100,2,9,3,1),(101,2,9,4,1),(102,2,9,5,1),(103,2,9,6,1),(104,2,9,7,1),(105,2,9,8,1),(106,2,9,9,1);
/*!40000 ALTER TABLE `seat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `student`
--

DROP TABLE IF EXISTS `student`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `student` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '主键ID',
  `student_id` varchar(20) NOT NULL COMMENT '学号（唯一）',
  `password` varchar(100) NOT NULL COMMENT '密码（加密存储）',
  `name` varchar(50) NOT NULL COMMENT '姓名',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `update_time` datetime DEFAULT NULL ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `student_id` (`student_id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='学生信息表';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `student`
--

LOCK TABLES `student` WRITE;
/*!40000 ALTER TABLE `student` DISABLE KEYS */;
INSERT INTO `student` VALUES (1,'2026001','123456','张三','2026-05-06 10:28:49',NULL),(2,'2026002','123456','李四','2026-05-06 10:28:49',NULL),(3,'2026003','123456','王五','2026-05-06 10:28:49',NULL),(4,'2024001','password123','张三','2026-05-06 15:36:24',NULL);
/*!40000 ALTER TABLE `student` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-05-06 16:43:14
