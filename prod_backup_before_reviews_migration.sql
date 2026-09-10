-- MySQL dump 10.13  Distrib 9.6.0, for macos26.2 (arm64)
--
-- Host: db-mysql-sfo2-60994-do-user-38846737-0.f.db.ondigitalocean.com    Database: defaultdb
-- ------------------------------------------------------
-- Server version	8.4.8

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
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('9cf535e60f7b');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `comments`
--

DROP TABLE IF EXISTS `comments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `comments` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `location_id` int NOT NULL,
  `experience` varchar(280) NOT NULL,
  `item_purchased` varchar(100) NOT NULL,
  `is_hidden` tinyint(1) NOT NULL DEFAULT '0',
  `price_paid` int DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_comments_location_id` (`location_id`),
  KEY `ix_comments_user_id` (`user_id`),
  CONSTRAINT `comments_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `comments_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `comments`
--

LOCK TABLES `comments` WRITE;
/*!40000 ALTER TABLE `comments` DISABLE KEYS */;
/*!40000 ALTER TABLE `comments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `invoices`
--

DROP TABLE IF EXISTS `invoices`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `invoices` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `map_id` int NOT NULL,
  `stripe_checkout_session_id` varchar(255) NOT NULL,
  `stripe_payment_intent_id` varchar(255) DEFAULT NULL,
  `stripe_customer_id` varchar(255) DEFAULT NULL,
  `amount` int NOT NULL,
  `currency` varchar(10) NOT NULL,
  `status` varchar(50) NOT NULL,
  `failure_reason` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `stripe_checkout_session_id` (`stripe_checkout_session_id`),
  UNIQUE KEY `stripe_payment_intent_id` (`stripe_payment_intent_id`),
  KEY `map_id` (`map_id`),
  KEY `ix_invoices_user_id` (`user_id`),
  CONSTRAINT `invoices_ibfk_1` FOREIGN KEY (`map_id`) REFERENCES `maps` (`id`) ON DELETE CASCADE,
  CONSTRAINT `invoices_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `invoices`
--

LOCK TABLES `invoices` WRITE;
/*!40000 ALTER TABLE `invoices` DISABLE KEYS */;
INSERT INTO `invoices` VALUES (1,1,1,'cs_test_a1TY7K38kb8Q9Lz4kuAawbG920VBk4ZXGEGhvohsf0bO5vw6TlelQxlZ1X','pi_3TmnJsFlqEWxut620axQHegN',NULL,1999,'usd','paid',NULL,'2026-06-27 03:54:18','2026-06-27 03:54:18'),(2,15,1,'cs_test_a1aTSUneoznBp8zdzuuO2hbLBzeQeaVNwLhoa1Bq5sscQyuVYeZc1DNEti','pi_3TnR7FFlqEWxut621Kuk9P0W',NULL,999,'usd','paid',NULL,'2026-06-28 22:23:55','2026-06-28 22:23:55'),(4,16,1,'cs_live_a17HaDLikpoyh09R04PbSnk4ez3bJLUNgEQkVs0mhMMXqeQEYE7m7P0pK8','pi_3TnWLxFiaew5RUEJ0eEh1VEN',NULL,999,'usd','paid',NULL,'2026-06-29 03:59:27','2026-06-29 03:59:27'),(5,19,1,'cs_live_a1I6930o2ZT0VevHBtmlXblbi8stuMNErVLHerdMQidqYweRSo74MfUog6','pi_3TnpChFiaew5RUEJ16uv9JYD',NULL,999,'usd','paid',NULL,'2026-06-30 00:07:09','2026-06-30 00:07:09'),(6,20,1,'cs_live_a1EOjrlmhUqB89YeYwbGkJ6Bdme21gxqgd9rLG4WE3RgKOeklJ7185sXry','pi_3TnstvFiaew5RUEJ1z6NPV0n',NULL,999,'usd','paid',NULL,'2026-06-30 04:04:02','2026-06-30 04:04:02'),(7,21,1,'cs_live_a1KKo4M8pFtP4iUoXKkbt4aD9zE3LGoP622AlyyZEzc31WelHyXaCetZu8','pi_3To1GkFiaew5RUEJ01A5WYWg',NULL,999,'usd','paid',NULL,'2026-06-30 13:00:09','2026-06-30 13:00:09'),(8,18,1,'cs_live_a1bmp2lV1nacylubRXc3RbX5wRPHmlKyldzZPtm95mIeoV1XEv8wthWsUt',NULL,NULL,999,'usd','expired',NULL,'2026-06-30 16:45:05','2026-06-30 16:45:05'),(9,22,1,'cs_live_a1tt2xmatMnryfq5yKKMpVCRBT23fmqwEYfgFWwgVaAS6gRYkSOsifpVwn','pi_3TocCvFiaew5RUEJ1JQzghdl',NULL,999,'usd','paid',NULL,'2026-07-02 04:26:40','2026-07-02 04:26:40'),(10,23,1,'cs_live_a15aZGKwWt4B68GvfB4t3Xetyvx0lZuJ0DIqSA5WmaGjq2WScLeVmDu5vG','pi_3Tq4Y4Fiaew5RUEJ0Jg4hZDz',NULL,999,'usd','paid',NULL,'2026-07-06 04:54:30','2026-07-06 04:54:30'),(11,24,1,'cs_live_a1J9yRWGRXB3I1qh1zqCdOJNV7CkfJC5Hhx7uednzTcY0qVd4Fcv7w8KAI','pi_3Ts387Fiaew5RUEJ0ZxaLKIt',NULL,999,'usd','paid',NULL,'2026-07-11 15:47:54','2026-07-11 15:47:54'),(12,25,1,'cs_live_a1gE5kEguHseqHNo1FN6iDjHlPhlObIkTzkZqUnxSBGZqKuEoFdzqVra9t','pi_3TuiKhFiaew5RUEJ1aboC5EQ',NULL,999,'usd','paid',NULL,'2026-07-19 00:11:55','2026-07-19 00:11:55'),(13,26,1,'cs_live_a19ZbHtjb36SOYZl2GhWpBswS3AYLG2zpStbPBiFyoWafvtB4sxUJvivZe',NULL,NULL,999,'usd','expired',NULL,'2026-07-20 18:55:05','2026-07-20 18:55:05'),(14,27,1,'cs_live_a11QQOIWtxe9pdxMkV7QFXmgpcbMoeQuJpV6AR6PFPClGuPmhapZZ00cVq','pi_3Tw8WOFiaew5RUEJ1szS1gTw',NULL,999,'usd','paid',NULL,'2026-07-22 22:21:51','2026-07-22 22:21:51'),(15,28,1,'cs_live_a1yyEYYjWNcKDiWA7TFnpePwKxWl6tfTTPoTdardKGzXbRQ52YmWNvcmcB','pi_3Tyy6SFiaew5RUEJ070aLniZ',NULL,999,'usd','paid',NULL,'2026-07-30 17:50:46','2026-07-30 17:50:46'),(16,30,1,'cs_test_a1idqo6dQaaBAltdgkGlwVhEUtncvXhCWjOVO7lscAOSpFp23AOQFJ2tZ6','pi_3TzMYjFlqEWxut620Rd2e4TA',NULL,999,'usd','paid',NULL,'2026-07-31 19:57:34','2026-07-31 19:57:34'),(17,31,1,'cs_live_a1ndlAxLn1uvzvwD79yvcGby6maQEbEaXE2FzGKdBGjiOHI4PxtlkZGGWd',NULL,NULL,999,'usd','expired',NULL,'2026-08-03 06:50:00','2026-08-03 06:50:00'),(18,32,1,'cs_live_a1EVWKi2sRycmFP2eFfqGqjR0mpffmV8LUrsrL2GmK7mpURIjm97m4QLce','pi_3U0P0pFiaew5RUEJ0LwHQDuh',NULL,999,'usd','paid',NULL,'2026-08-03 16:46:54','2026-08-03 16:46:54'),(19,33,1,'cs_live_a1RABIKoSivhF1SUvt2IBNg8PoZGReiP8IU2DB4YnCmXjlZV4qE2srAsyw','pi_3UABq9Fiaew5RUEJ0h5OyIWT',NULL,999,'usd','paid',NULL,'2026-08-30 16:44:19','2026-08-30 16:44:19');
/*!40000 ALTER TABLE `invoices` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `location_hours`
--

DROP TABLE IF EXISTS `location_hours`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `location_hours` (
  `id` int NOT NULL AUTO_INCREMENT,
  `location_id` int NOT NULL,
  `day_of_week` smallint NOT NULL,
  `open_time` time DEFAULT NULL,
  `close_time` time DEFAULT NULL,
  `is_closed` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  KEY `ix_location_hours_location_id` (`location_id`),
  CONSTRAINT `location_hours_ibfk_1` FOREIGN KEY (`location_id`) REFERENCES `locations` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1059 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `location_hours`
--

LOCK TABLES `location_hours` WRITE;
/*!40000 ALTER TABLE `location_hours` DISABLE KEYS */;
INSERT INTO `location_hours` VALUES (786,97,0,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(787,97,1,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(788,97,2,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(789,97,3,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(790,97,4,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(791,97,5,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(792,97,6,'09:00:00','21:00:00',0,'2026-06-30 03:48:11','2026-06-30 03:48:11'),(793,98,0,'11:00:00','20:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(794,98,1,'11:00:00','20:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(795,98,2,'11:00:00','20:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(796,98,3,'11:00:00','20:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(797,98,4,'11:00:00','20:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(798,98,5,'11:00:00','20:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(799,98,6,'11:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(800,99,0,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(801,99,1,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(802,99,2,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(803,99,3,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(804,99,4,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(805,99,5,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(806,99,6,'10:00:00','19:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(807,100,0,NULL,NULL,1,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(808,100,1,'10:00:00','16:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(809,100,2,NULL,NULL,1,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(810,100,3,NULL,NULL,1,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(811,100,4,'10:00:00','16:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(812,100,5,'10:00:00','16:00:00',0,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(813,100,6,NULL,NULL,1,'2026-06-30 03:48:12','2026-06-30 03:48:12'),(814,101,0,'12:00:00','16:30:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(815,101,1,'12:00:00','16:30:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(816,101,2,'12:00:00','16:30:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(817,101,3,'12:00:00','16:30:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(818,101,4,'12:00:00','16:30:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(819,101,5,'12:00:00','16:30:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(820,101,6,NULL,NULL,1,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(821,102,0,'11:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(822,102,1,'11:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(823,102,2,'11:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(824,102,3,'11:00:00','20:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(825,102,4,'11:00:00','20:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(826,102,5,'11:00:00','20:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(827,102,6,'11:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(828,103,0,'12:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(829,103,1,'12:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(830,103,2,'12:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(831,103,3,'12:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(832,103,4,'12:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(833,103,5,'12:00:00','19:00:00',0,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(834,103,6,NULL,NULL,1,'2026-06-30 03:48:13','2026-06-30 03:48:13'),(835,104,0,'12:00:00','19:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(836,104,1,'12:00:00','19:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(837,104,2,'12:00:00','19:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(838,104,3,'12:00:00','19:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(839,104,4,'12:00:00','19:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(840,104,5,'12:00:00','19:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(841,104,6,'12:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(842,105,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(843,105,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(844,105,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(845,105,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(846,105,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(847,105,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(848,105,6,NULL,NULL,1,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(849,106,0,NULL,NULL,1,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(850,106,1,NULL,NULL,1,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(851,106,2,'12:00:00','18:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(852,106,3,'12:00:00','18:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(853,106,4,'12:00:00','18:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(854,106,5,'12:00:00','18:00:00',0,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(855,106,6,NULL,NULL,1,'2026-06-30 03:48:14','2026-06-30 03:48:14'),(856,107,0,NULL,NULL,1,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(857,107,1,'12:00:00','16:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(858,107,2,'12:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(859,107,3,'12:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(860,107,4,'12:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(861,107,5,'11:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(862,107,6,'11:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(863,108,0,'10:00:00','16:30:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(864,108,1,'10:00:00','16:30:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(865,108,2,'10:00:00','16:30:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(866,108,3,'10:00:00','16:30:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(867,108,4,'10:00:00','16:30:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(868,108,5,'10:00:00','16:30:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(869,108,6,NULL,NULL,1,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(870,109,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(871,109,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(872,109,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(873,109,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(874,109,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(875,109,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(876,109,6,NULL,NULL,1,'2026-06-30 03:48:15','2026-06-30 03:48:15'),(877,110,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(878,110,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(879,110,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(880,110,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(881,110,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(882,110,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(883,110,6,NULL,NULL,1,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(884,111,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(885,111,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(886,111,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(887,111,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(888,111,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(889,111,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(890,111,6,'11:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(891,112,0,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(892,112,1,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(893,112,2,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(894,112,3,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(895,112,4,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(896,112,5,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(897,112,6,'07:00:00','17:00:00',0,'2026-06-30 03:48:16','2026-06-30 03:48:16'),(898,113,0,'11:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(899,113,1,'11:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(900,113,2,'11:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(901,113,3,'11:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(902,113,4,'14:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(903,113,5,'11:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(904,113,6,NULL,NULL,1,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(905,114,0,'09:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(906,114,1,'09:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(907,114,2,'09:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(908,114,3,'09:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(909,114,4,'09:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(910,114,5,'09:00:00','19:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(911,114,6,'10:00:00','18:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(912,115,0,'08:30:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(913,115,1,'08:30:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(914,115,2,'08:30:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(915,115,3,'08:30:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(916,115,4,'08:30:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(917,115,5,'08:30:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(918,115,6,'10:00:00','17:00:00',0,'2026-06-30 03:48:17','2026-06-30 03:48:17'),(919,116,0,'11:00:00','19:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(920,116,1,'11:00:00','19:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(921,116,2,'11:00:00','19:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(922,116,3,'11:00:00','19:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(923,116,4,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(924,116,5,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(925,116,6,'11:00:00','19:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(926,117,0,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(927,117,1,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(928,117,2,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(929,117,3,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(930,117,4,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(931,117,5,'11:00:00','20:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(932,117,6,'11:00:00','19:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(933,118,0,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(934,118,1,'11:00:00','18:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(935,118,2,'11:00:00','18:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(936,118,3,'11:00:00','18:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(937,118,4,'11:00:00','18:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(938,118,5,'11:00:00','18:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(939,118,6,'11:00:00','18:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(940,119,0,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(941,119,1,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(942,119,2,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(943,119,3,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(944,119,4,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(945,119,5,'10:00:00','14:00:00',0,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(946,119,6,NULL,NULL,1,'2026-06-30 03:48:18','2026-06-30 03:48:18'),(947,120,0,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(948,120,1,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(949,120,2,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(950,120,3,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(951,120,4,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(952,120,5,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(953,120,6,'10:00:00','19:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(954,121,0,'09:00:00','18:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(955,121,1,'09:00:00','18:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(956,121,2,'09:00:00','18:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(957,121,3,'09:00:00','18:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(958,121,4,'09:00:00','18:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(959,121,5,'09:00:00','18:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(960,121,6,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(961,122,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(962,122,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(963,122,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(964,122,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(965,122,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(966,122,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(967,122,6,NULL,NULL,1,'2026-06-30 03:48:19','2026-06-30 03:48:19'),(968,123,0,NULL,NULL,1,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(969,123,1,NULL,NULL,1,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(970,123,2,'10:00:00','16:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(971,123,3,'10:00:00','16:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(972,123,4,'10:00:00','16:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(973,123,5,'10:00:00','16:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(974,123,6,NULL,NULL,1,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(975,124,0,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(976,124,1,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(977,124,2,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(978,124,3,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(979,124,4,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(980,124,5,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(981,124,6,'11:00:00','17:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(982,125,0,'10:00:00','19:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(983,125,1,'10:00:00','19:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(984,125,2,'10:00:00','19:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(985,125,3,'10:00:00','19:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(986,125,4,'10:00:00','19:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(987,125,5,'10:00:00','19:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(988,125,6,'11:00:00','18:00:00',0,'2026-06-30 03:48:20','2026-06-30 03:48:20'),(989,126,0,'09:00:00','19:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(990,126,1,'09:00:00','19:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(991,126,2,'09:00:00','19:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(992,126,3,'09:00:00','19:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(993,126,4,'09:00:00','19:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(994,126,5,'09:00:00','19:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(995,126,6,'10:00:00','18:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(996,127,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(997,127,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(998,127,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(999,127,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1000,127,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1001,127,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1002,127,6,NULL,NULL,1,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1003,128,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1004,128,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1005,128,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1006,128,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1007,128,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1008,128,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1009,128,6,NULL,NULL,1,'2026-06-30 03:48:21','2026-06-30 03:48:21'),(1010,129,0,'10:00:00','19:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1011,129,1,'10:00:00','19:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1012,129,2,'10:00:00','19:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1013,129,3,'10:00:00','19:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1014,129,4,'10:00:00','19:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1015,129,5,'10:00:00','19:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1016,129,6,'11:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1017,130,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1018,130,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1019,130,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1020,130,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1021,130,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1022,130,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1023,130,6,NULL,NULL,1,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1024,131,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1025,131,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1026,131,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1027,131,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1028,131,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1029,131,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1030,131,6,NULL,NULL,1,'2026-06-30 03:48:22','2026-06-30 03:48:22'),(1031,132,0,'10:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1032,132,1,'10:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1033,132,2,'10:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1034,132,3,'10:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1035,132,4,'10:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1036,132,5,'10:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1037,132,6,'11:00:00','17:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1038,133,0,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1039,133,1,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1040,133,2,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1041,133,3,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1042,133,4,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1043,133,5,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1044,133,6,NULL,NULL,1,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1045,134,0,NULL,NULL,1,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1046,134,1,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1047,134,2,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1048,134,3,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1049,134,4,'10:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1050,134,5,'12:00:00','16:00:00',0,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1051,134,6,NULL,NULL,1,'2026-06-30 03:48:23','2026-06-30 03:48:23'),(1052,135,0,'11:00:00','16:00:00',0,'2026-06-30 03:48:24','2026-06-30 03:48:24'),(1053,135,1,'11:00:00','16:00:00',0,'2026-06-30 03:48:24','2026-06-30 03:48:24'),(1054,135,2,'11:00:00','16:00:00',0,'2026-06-30 03:48:24','2026-06-30 03:48:24'),(1055,135,3,'11:00:00','16:00:00',0,'2026-06-30 03:48:24','2026-06-30 03:48:24'),(1056,135,4,'11:00:00','16:00:00',0,'2026-06-30 03:48:24','2026-06-30 03:48:24'),(1057,135,5,'11:00:00','16:00:00',0,'2026-06-30 03:48:24','2026-06-30 03:48:24'),(1058,135,6,NULL,NULL,1,'2026-06-30 03:48:24','2026-06-30 03:48:24');
/*!40000 ALTER TABLE `location_hours` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `locations`
--

DROP TABLE IF EXISTS `locations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `locations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `map_id` int NOT NULL,
  `latitude` float NOT NULL,
  `longitude` float NOT NULL,
  `min_price` int DEFAULT NULL,
  `max_price` int DEFAULT NULL,
  `price_level` int DEFAULT NULL,
  `description` varchar(1024) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `google_place_id` varchar(255) DEFAULT NULL,
  `neighborhood` varchar(255) NOT NULL DEFAULT 'Unknown',
  PRIMARY KEY (`id`),
  KEY `ix_locations_map_id` (`map_id`),
  CONSTRAINT `locations_ibfk_1` FOREIGN KEY (`map_id`) REFERENCES `maps` (`id`) ON DELETE CASCADE,
  CONSTRAINT `chk_locations_price_level` CHECK ((`price_level` in (1,2,3)))
) ENGINE=InnoDB AUTO_INCREMENT=136 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `locations`
--

LOCK TABLES `locations` WRITE;
/*!40000 ALTER TABLE `locations` DISABLE KEYS */;
INSERT INTO `locations` VALUES (97,'Goodwill - Fillmore',1,37.785,-122.433,499,1999,1,'Goodwill can really be hit or miss. But I found some really awesome blazers here. A good blazer selection to me is one that has a variety of styles, sizes, and a wide range of brands. Blazer price range: $9.99 - $16.99. This range is pretty typical for Goodwill these days (which is higher than it should be), but only worth it sometimes. Look for things you don\'t think you can easily find again. Shoes: $5.99 - $7.99, Short/long sleeve tops: $4.99 - $11.99, Pants: $7.99 - $9.99.','2026-06-30 03:48:11','2026-06-30 03:48:46','ChIJr-8JULiAhYAR9kI2xSxQ0CY','Unknown'),(98,'Buffalo Exchange - Haight',1,37.7698,-122.448,1500,2600,2,'The best Buffalo Exchange I\'ve ever been to (and I\'ve been to my fair share). Buffalo Exchange is a chain secondhand store, so prices are higher. But this is one I would not skip. Surrounded by some of the most expensive vintage stores in the city, this Buffalo Exchange carries clothing of the same quality for significantly less. They carry lots of modern pieces, but they have tons of amazing vintage brands, some of which I had never heard of. Great condition. I\'d shop here for blouses. Tons of fun work-appropriate blouses. Blouse price average: $19; cool skirts too. Skirt price average: $15. Shoes: $22 - $45.','2026-06-30 03:48:11','2026-06-30 03:48:46','ChIJlY_nPFOHhYAR4Vi_wsIX4I4','Unknown'),(99,'Treasure Paws Thrift',1,37.5864,-122.363,700,3500,2,'Has a regular section and a better brands section, but not a super clear line between what counts for each category. Regular tops and pants: $7 - $12; \"Better brands\" tops and pants $15 - $25, sometimes a little higher for designer ($39 for Ulla Johnson pants). Dresses: $14 - $23. Overall, they have a ton of inventory that is pretty well curated without turning into a vintage store. Amazing shoe selection with brands like Nine West and Diba. If you go up to the counter with a haul, ask sweetly if they can do \"any better\" on an item.','2026-06-30 03:48:12','2026-06-30 03:48:47','ChIJcy2zSyR2j4ARRzgfpyxa9mM','Unknown'),(100,'Turnstyle Thrift Shop',1,37.5685,-122.325,400,1500,1,'Overall, there\'s a good amount to look through. It\'s organized. Not every item is a winner (it never is), but I liked the blouse section a lot. They had great jewelry too. It\'s next to St. Vincent de Paul of San Mateo so you should stop in if you\'re in the area. Blouses: about $6 - $10. Pants: $4 - $8. Designer section: $10 - $18. Jewelry: about $13 - $15.','2026-06-30 03:48:12','2026-06-30 03:48:47','ChIJvUs43naej4ARlDtRgmZPkA4','Unknown'),(101,'5th Avenue Family Thrift Mart',1,37.4855,-122.227,199,1500,1,'Blouses: $2.99 - $4.99, some $1.99 on sale. Pants: $4.99 - $8.99. Shoes: heels $7.50, flats $5, boots $12-$15. Skirts: $4.99. Dresses: $5.99 unless tag says otherwise. Current sale: 50% off of most items above $10. I found some serious gems here. The female owner is so sweet. She told me that she doesn\'t know how they\'re still open because of the (lack of) foot traffic and low price points. Let\'s keep her in business!','2026-06-30 03:48:12','2026-06-30 03:48:47','ChIJ1XtG4G2jj4AR6M-824qmhkQ','Unknown'),(102,'Valencia Street Vintage',1,37.7614,-122.422,1000,1500,1,'Vintage vintage inside, out of my price range, but there\'s a covered section outside in front of the store with a couple racks of clothing that are $10 - $15. Seemingly some of the things that don\'t sell inside. The outdoor selection was really good, and had a surprising amount of fun work-appropriate attire.','2026-06-30 03:48:13','2026-06-30 03:48:47','ChIJxdzdJuB_j4AROOYTI-zWUbM','Unknown'),(103,'Eye Thrift',1,37.7527,-122.421,800,2500,1,'Super small store and mainly clothing that feels more street style, but there were pieces mixed in that were surprisingly unique and work appropriate. Some of my favorite brands to find thrifting: Eileen Fisher and St. John. Long sleeve blouses: $7.99/$8.99 (including an Eileen Fisher top). Sweaters: $7.99 - $12.99. Skirts: $8.99 - $14.99 for a real leather skirt. Trench coat for $14.99. I wouldn\'t say I would go out of my way to shop here, but if you\'re in the area, you just might find one or two things you love.','2026-06-30 03:48:13','2026-06-30 03:48:47','ChIJH_3m1sB_j4ARRhPlRlvZxB8','Unknown'),(104,'Born Again Thrift',1,37.7605,-122.419,1200,4500,2,'One of the stores at the top of the price bracket with clothing averaging $19. But this curation of clothing is honestly some of the best I\'ve seen. Tons of rare & one-of-a-kind items that were incredibly fair price wise. Lots of work-appropriate Y2K pieces. Curation upcharge, but item-dependent. I bought a pair of Ulla Johnson jeans for $25...they retail for almost $400. Pants: $18-25 average. Belts (real leather): $12.99 - $14.99. Blouses: Sleeveless $12-$14, Short-sleeve $14.99-$24.99, Long-sleeve $14.99-$34.99. Skirts: $15-$20 mostly, vintage suede skirts $25 & $30. Sweaters: $15-$35.','2026-06-30 03:48:13','2026-06-30 03:48:47','ChIJQYVosuJ_j4ARHfk5AdQe21I','Unknown'),(105,'St. Vincent de Paul Thrift Store',1,37.5682,-122.325,400,1800,1,'One of the best shops I visited in the Bay Area. This is a small location, but probably 10+ round clothing racks with tons of gems. I was finding things left and right. Every clothing category is pretty much the same price, no matter the brand...and I found Theory and high-end vintage brands. Everything was in amazing condition. I bought multiple pairs of dress pants, skirts, blazers, suit sets, and a necklace. Short sleeves: $4 - $7. Long sleeves: $5 - $7. Pants: $7. Blazers: $15. Skirts: $4 - $7.','2026-06-30 03:48:14','2026-06-30 03:48:47','ChIJf7nCIHeej4AR1sNRh2yFr0E','Unknown'),(106,'Dorothy\'s Closet',1,37.8664,-122.256,600,1700,1,'Standard pricing for every category on signs throughout the store: Coats $17. Vests $11. Jackets $15. Blazers $15. Shoes $10. Boots $13. Skirts $11. Sweatshirts and sweaters $11. Pants $11. Short sleeve blouses $9. Long sleeve blouses $11. T-shirts and tanks $7. Belts, scarves, hats, neckties $6 or priced as marked. Lots of Y2K and lots of nice pants with a huge range of sizes.','2026-06-30 03:48:14','2026-06-30 03:48:47','ChIJ0X6DOAB9hYARHrKBPmHsB3A','Unknown'),(107,'Thrifty Kitty',1,37.7724,-122.27,500,8000,2,'The racks in the store are a little overpriced and vary significantly, but they have a $10 rack outside with the stuff that doesn\'t sell after a while. I bought an Alice & Olivia blouse from this rack. Inside, blouse prices varied by brand. Blouses: $5 - $24 with some specialty tops up to $35. $40 cashmere sweater. $80 Bergdorf Goodman jacket. $75 Eileen Fisher jacket. $45 Lafayette 148 blazer. Skirts: $9 - $15. Ties: $5.','2026-06-30 03:48:14','2026-06-30 03:48:47','ChIJqTE8-liBj4ARlgDdQLAzJUk','Unknown'),(108,'Discovery Shop - Walnut Creek',1,37.8934,-122.06,700,2000,1,'Every Discovery Shop is different but for the most part the pricing stays pretty consistent (so much so that it\'s noticeable when you go to one that overcharges for things you know other locations price lower). Blouse/top prices: $8 - $10 (including for brands like Facconable and J. Crew). Pants: $7 - $12. I really liked the selection at this particular Discovery Shop.','2026-06-30 03:48:15','2026-06-30 03:48:47','ChIJ5QuDSpVhhYARz4cuELbaAGs','Unknown'),(109,'Discovery Shop - Menlo Park',1,37.4526,-122.182,600,2000,1,'Every Discovery Shop is different but for the most part the pricing stays pretty consistent. I\'ll always recommend this thrift store chain. They get amazing donations.','2026-06-30 03:48:15','2026-06-30 03:48:47','ChIJq-45GrCkj4ARkxa7VPgWhSU','Unknown'),(110,'Discovery Shop - Sunnyvale',1,37.3584,-122.023,600,2500,1,'Every Discovery Shop is different but for the most part the pricing stays pretty consistent. I\'ll always recommend this thrift store chain. They get amazing donations...this location was insane. Maybe it was my lucky day but everything I loved fit me perfectly. Left with what looked like super 90s minimalist workwear pieces.','2026-06-30 03:48:15','2026-06-30 03:48:47','ChIJVVVVVdG1j4ARmOfN_kUsfts','Unknown'),(111,'Discovery Shop - Oakland',1,37.8263,-122.252,800,2500,1,'Great selection here. A well-balanced mix of vintage and modern brands. Average price was $8-$12 for all categories of clothing. Most everything was fairly priced, but there are always a few outliers. I thrifted a Ba&sh top here for $25; retail is $200+. Not all Discovery Shops are created equal - prices are decentralized, so some locations charge more for the same quality, style, and brand. The more expensive the area, the more likely they\'ll up-charge. BUT I\'d check out this location.','2026-06-30 03:48:16','2026-06-30 03:48:48','ChIJwbF8D_d9hYARhLkceZOxeG4','Unknown'),(112,'Goodwill Bins - South San Francisco',1,37.6555,-122.41,179,179,1,'Goodwill Bins are not for everyone. You\'re in a warehouse, waiting for staff to bring out gigantic bins of clothing that you dig through...it\'s not always pleasant. But, if you go without expectations, you won\'t be disappointed and you might find some incredible things. I would say it\'s better to start with thrift stores so you can pinpoint your style first. The Bay Area secondhand scene is super popular, so going to the bins here was actually more successful than I thought. I found cute dresses, blouses, and jackets. Price: $1.79/lb.','2026-06-30 03:48:16','2026-06-30 03:48:48','ChIJ5zaBX4h5j4AR9Y7XD1vQJ00','Unknown'),(113,'The EcoCloset',1,37.7095,-122.45,599,999,1,'A limited selection of clothing for work and not everything was of the best quality, but I left with a skirt and jacket I loved. If you\'re in the area you might as well check it out and hopefully get lucky. Skirts, tops, jackets were all $5.99 - $9.99.','2026-06-30 03:48:16','2026-06-30 03:48:48','ChIJi7tA8RB9j4ARIFuHhB-INHk','Unknown'),(114,'Salvation Army Family Thrift - Geary',1,37.7812,-122.462,699,1399,1,'One of the best Salvation Army stores I\'ve ever been to, and I almost didn\'t stop by! It\'s two stories, with racks of shoes on the first floor and most of the clothing on the second floor. I honestly spent hours here. I found work appropriate clothing in every category. I bought multiple Diane Von Furstenburg clothing items, found some really cool vintage jackets and maybe my favorite work pants ever. Trust me.','2026-06-30 03:48:17','2026-06-30 03:48:48','ChIJq_N8GzmHhYARqRDXdOCwpcA','Unknown'),(115,'Urban Ore',1,37.8624,-122.29,300,3500,1,'This spot is a \"salvage yard,\" so there\'s a ton of stuff here, but they have a small, organized clothing section. They even have a dressing room, which is more uncommon than you might think. Everything from vintage dresses to work pants to blouses and sweaters. Jewelry and other accessories too. Most people probably don\'t know they carry clothing...but now you do. And I highly recommend a visit. Such cool stuff for incredible prices. The staff is really nice too. Most items $3 - $10, designer items $10 - $35.','2026-06-30 03:48:17','2026-06-30 03:48:48','ChIJ4_xtcPV-hYARCrPBfPLtLfE','Unknown'),(116,'Vanishing Point Vintage',1,37.8369,-122.262,500,8000,2,'Real vintage at a great price. Organized by decade, curated, color coded. Everything from 1940\'s - Y2K. Lots of 70\'s. This is a great spot to drop by for business casual attire. Prices are not inexpensive, but I would come back here just for their selection of vintage Levi\'s. I spent $65 each on two pairs that would have cost me over $200 near where I live in LA. Average prices: $20-$30. Blouses: $14-$35. Y2K & 90\'s tops: $5-$32 (mainly $18-$25). Skirts: $5-$30.','2026-06-30 03:48:17','2026-06-30 03:48:48','ChIJgz8TFgB9hYAR45hirT-TL10','Unknown'),(117,'Crossroads Trading',1,37.8433,-122.252,1500,4700,2,'Crossroads is a chain secondhand store, focused mainly on curated modern brands. I did see more unique vintage brands at this location than I have at others. The price points reflect the curation, but worth a look for a couple special items. One category I\'m unlikely to purchase at Crossroads: shoes - way overpriced. Blazers are up there too ($30-$40 each). Blouses (short & long sleeve): lower end $18.50, average $22.50, higher end $32+. Skirts: $15-$18.50. Pants: $22.50-$32.50. Dresses: $24-$47. Blazers: $24-$28.','2026-06-30 03:48:18','2026-06-30 03:48:48','ChIJlV96mMR9hYARINtHTTHMEC4','Unknown'),(118,'Thrift Shop Supporting Berkeley Humane',1,37.8568,-122.253,1200,8000,2,'New store, priced like a vintage shop and (some) online resellers. The best thrift shops are the ones that price the same/similar items lower than listing prices for resale online. Here, a J. Crew blouse was $17, which is super high for an in-person experience. Some items for $10-$14, but very few. So why am I including it on the map? Their selection. Brands you\'ll find at most thrift stores, but unique pieces from those brands. Tracy Reese for example. Average: $17-$27, with higher prices for brand names.','2026-06-30 03:48:18','2026-06-30 03:48:48','ChIJsQuRc9R5hYARWNG2b9v-QpU','Unknown'),(119,'Thrift Shop St. Matthew\'s Episcopal Church',1,37.5628,-122.324,400,1800,1,'Open 10 months out of the year because the store is run by volunteers. Don\'t underestimate unassuming shops like these. People love to donate to thrift stores that go to causes they care about. Never skip a thrift shop associated with a church. I left with two Elie Tahari suit sets in perfect condition for $15 a set.','2026-06-30 03:48:18','2026-06-30 03:48:48','ChIJeRQAYHGej4ARSHsW63foG-U','Unknown'),(120,'Community Thrift Store (CTS)',1,37.7629,-122.421,600,4000,2,'Everyone raves about Community Thrift but to be honest, I think the clothing is a bit overpriced for what it is. Shoes: $12 - $28. Dresses: $7.95 - $25.35. Pants: $10.95 for H&M (almost like buying new). Talbots: $8.95 - $28.95. Coats: $15.95 - $22.95 for Ann Taylor. $22.95 for Theory (amazing even if high for a thrift store). Tops: $5.95 for a J. Crew tank. I would still check it out, but manage your expectations.','2026-06-30 03:48:19','2026-06-30 03:48:48','ChIJMa1S2SJ-j4ARGGpY5HQ85sE','Unknown'),(121,'Thrift Center Thrift Store',1,37.5073,-122.26,499,1599,1,'Loved the selection here! I found a couple really great Brooks Brothers collared shirts in pristine condition, as well as some great basic pencil skirts. Blouses: $6.99 - $9.99. Skirts: $4.99 - $6.99. They had a 25% off sale going for a specific color (many stores do this).','2026-06-30 03:48:19','2026-06-30 03:48:48','ChIJIbdDcReij4ARQvG9W-0FfeA','Unknown'),(122,'Discovery Shop - San Jose',1,37.2638,-121.868,600,2500,1,'Every Discovery Shop is different but for the most part the pricing stays pretty consistent. I\'ll always recommend this thrift store chain. They get amazing donations. Loved this location too. Not as picked over as some others.','2026-06-30 03:48:19','2026-06-30 03:48:48','ChIJEW3lusEzjoARERsxD-zFlVQ','Unknown'),(123,'Thrift Box',1,37.308,-121.891,600,2000,1,'Lots of clothing categories priced fairly, but they overcharge for some name brands. Even still there\'s a huge variety of vintage and modern clothing items. I made multiple purchases here. Coats and jackets: $7 - $8. Skirts: $6 - $8.','2026-06-30 03:48:20','2026-06-30 03:48:49','ChIJP5aVOFkzjoARehGjqdvUpNU','Unknown'),(124,'Briarwood Antiques and Collectibles',1,37.319,-121.918,100,2500,1,'Vintage/antique mall that has tons of affordable vintage jewelry and accessories. Such a cool place to get lost in. There\'s some clothing here, but not much and it\'s on the more expensive side. Adding fun accessories to work outfits is one of the best ways to show off your personality. Think bangles, necklaces, earrings, brooches!','2026-06-30 03:48:20','2026-06-30 03:48:49','ChIJ-Zb0zz7Lj4ARnWbjy0uUZaM','Unknown'),(125,'HopeTHRIFT San Jose',1,37.2966,-121.866,499,1299,1,'HopeThrift is what Savers wants to be. Just solid and fair all around. Huge store. Shoes: $6.99 - $12.99. Great flats and low kitten heels. Pants: $5.99 and up. Blazers: $6.99 - $12.99. Sweaters: $4.99 - $7.99. Skirts: $6.99 - $10.99. Dresses: $7.99 and up. The dress selection here was better than so many I\'ve seen. Just really unique pieces and vintage labels I hadn\'t heard of. And they have dressing rooms!','2026-06-30 03:48:20','2026-06-30 03:48:49','ChIJff7TKg0zjoARFVcXY8U77gs','Unknown'),(126,'Salvation Army - San Rafael',1,37.9735,-122.531,499,999,1,'One of the messier Salvation Army stores I\'ve been in. Clothing on the floor and hangers sticking out all over the place. Normally I would say don\'t even bother, but I ended up finding some great basic skirts here, and I saw jackets I liked too. Pants: $8.99. Skirts: $4.99 - $6.99. Jackets/Blazers: $6.99 - $8.99.','2026-06-30 03:48:21','2026-06-30 03:48:49','ChIJKTSqEfWZhYARvN-f5kfEt-E','Unknown'),(127,'Hodgepodge Thrift Store - San Rafael',1,37.962,-122.513,400,1500,1,'Another favorite of mine. So much to choose from, super nice brands, so many things with so much personality, all for prices I didn\'t feel the need to negotiate. Women\'s tops were $7 - $12 no matter the brand. L\'Agence tops for $12, a Marc Jacobs dress for $10. The store was full of eclectic shoppers and that\'s always a good sign.','2026-06-30 03:48:21','2026-06-30 03:48:49','ChIJTbXOIfeZhYARApDI0k1kFJQ','Unknown'),(128,'Hodgepodge Thrift Store - Novato',1,38.1077,-122.572,400,1500,1,'Another favorite of mine and a sister to the other Hodgepodge store. I found more in their San Rafael location, but there was so much to choose from, super nice brands, so many things with so much personality, all for prices I didn\'t feel the need to negotiate. This location was also full of eclectic shoppers and that\'s always a good sign.','2026-06-30 03:48:21','2026-06-30 03:48:49','ChIJU_R972K7hYARhqs0C4U753w','Unknown'),(129,'Flipside Thrift',1,38.11,-122.565,699,1699,1,'A great spot to find blazers and pants. Lots to look through, some vintage, some modern. Prices were fair enough. Blazers: $7.99 - $16.99.','2026-06-30 03:48:22','2026-06-30 03:48:49','ChIJQ8g6FwC7hYAR8D6egAqBrak','Unknown'),(130,'Discovery Shop - Novato',1,38.1043,-122.577,600,2000,1,'Every Discovery Shop is different but for the most part the pricing stays pretty consistent. I\'ll always recommend this thrift store chain. They get amazing donations. Short/long sleeves: $5 - $18. Skirts: $8. Pants: $10 - $13. Tahari blazer: $20.','2026-06-30 03:48:22','2026-06-30 03:48:49','ChIJSRyFS7-9hYARgmf7nf8eAo4','Unknown'),(131,'Rescued Treasures',1,37.908,-122.053,800,1100,1,'One of the best thrift stores I visited in the Bay Area and it was in a tiny strip mall. I bought at least 10 items from here, and everything was about $10. Theory, Linda Allen Ellen Tracy, Vince, so many more amazing brands for insane prices in amazing condition. Really big selection and really nice staff.','2026-06-30 03:48:22','2026-06-30 03:48:49','ChIJT3LUpMRhhYARnE9W0V8FGJ8','Unknown'),(132,'Hospice Thrift Shoppes',1,37.8936,-122.06,500,1000,1,'Another amazing chain. Left with blouses and dresses. Everything was $5 - $10.','2026-06-30 03:48:23','2026-06-30 03:48:49','ChIJdyErRcNhhYAR1cF9fq2DebA','Unknown'),(133,'Mt Carmel Shop',1,37.906,-122.549,500,6000,2,'Really fun vintage jewelry, earrings were $7 - $12. Regular standard prices: Blouses $5, Dresses $6, Skirts $5. Plus a higher end section: $12 and up, $30 average. Some nice things - Theory pants for $18, Ba&sh for $25, suit set for $50/60.','2026-06-30 03:48:23','2026-06-30 03:48:49','ChIJhzuTkG2QhYARm1bMQHzvR78','Unknown'),(134,'St Patrick\'s Thrift Shop',1,37.934,-122.536,200,800,1,'SUPER small - like one rack small - but I found a really cool long sleeve top that looks like something on my Pinterest board. Worth checking out if in the area. Most items $2 - $8, random items $20 - $30.','2026-06-30 03:48:23','2026-06-30 03:48:49','ChIJv5LiO3iahYAR2FFNCqcJWNo','Unknown'),(135,'Marin Humane Thrift Shop',1,37.9745,-122.561,900,1900,1,'I found some nice blouses here. The selection was okay, but including it because I think it\'ll have better days. There was real vintage mixed into modern items. Prices: $9 - $19.','2026-06-30 03:48:24','2026-06-30 03:48:50','ChIJmci2sT-XhYARg532rHnwZmQ','Unknown');
/*!40000 ALTER TABLE `locations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `maps`
--

DROP TABLE IF EXISTS `maps`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `maps` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `slug` varchar(255) NOT NULL,
  `region` varchar(255) DEFAULT NULL,
  `price` int NOT NULL,
  `description` varchar(512) DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  `status` enum('live','waitlist','dropped') NOT NULL DEFAULT 'waitlist',
  PRIMARY KEY (`id`),
  UNIQUE KEY `name` (`name`),
  UNIQUE KEY `slug` (`slug`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `maps`
--

LOCK TABLES `maps` WRITE;
/*!40000 ALTER TABLE `maps` DISABLE KEYS */;
INSERT INTO `maps` VALUES (1,'Bay Area','Bay-Area-CA','Bay Area, CA',999,'San Francisco, the East Bay, the Peninsula, the South Bay through San Jose, and Marin up through Petaluma.','2026-06-27 03:44:53','2026-06-27 03:44:53','live'),(2,'Los Angeles','los-angeles-ca','Los Angeles, CA',999,'Join the waitlist to be notified when this map launches.','2026-08-07 22:04:26','2026-08-07 22:04:26','waitlist'),(3,'Manhattan','manhattan-ny','Manhattan, NY',1299,'Join the waitlist to be notified when this map launches.','2026-08-07 22:04:26','2026-08-07 22:04:26','waitlist'),(4,'Brooklyn/Queens','brooklyn-queens-ny','Brooklyn/Queens, NY',999,'Join the waitlist to be notified when this map launches.','2026-08-07 22:04:26','2026-08-07 22:04:26','waitlist'),(5,'Maricopa County','maricopa-county-az','Maricopa County, AZ',999,'Join the waitlist to be notified when this map launches.','2026-08-07 22:04:26','2026-08-07 22:04:26','waitlist');
/*!40000 ALTER TABLE `maps` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `purchases`
--

DROP TABLE IF EXISTS `purchases`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchases` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `map_id` int NOT NULL,
  `invoice_id` int NOT NULL,
  `purchased_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_map_purchase` (`user_id`,`map_id`),
  KEY `invoice_id` (`invoice_id`),
  KEY `map_id` (`map_id`),
  CONSTRAINT `purchases_ibfk_1` FOREIGN KEY (`invoice_id`) REFERENCES `invoices` (`id`),
  CONSTRAINT `purchases_ibfk_2` FOREIGN KEY (`map_id`) REFERENCES `maps` (`id`) ON DELETE CASCADE,
  CONSTRAINT `purchases_ibfk_3` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `purchases`
--

LOCK TABLES `purchases` WRITE;
/*!40000 ALTER TABLE `purchases` DISABLE KEYS */;
INSERT INTO `purchases` VALUES (1,1,1,1,'2026-06-27 03:54:18'),(2,15,1,2,'2026-06-28 22:23:55'),(3,16,1,4,'2026-06-29 03:59:28'),(4,19,1,5,'2026-06-30 00:07:09'),(5,20,1,6,'2026-06-30 04:04:02'),(6,21,1,7,'2026-06-30 13:00:09'),(7,22,1,9,'2026-07-02 04:26:40'),(8,23,1,10,'2026-07-06 04:54:30'),(9,24,1,11,'2026-07-11 15:47:54'),(10,25,1,12,'2026-07-19 00:11:55'),(11,27,1,14,'2026-07-22 22:21:51'),(12,28,1,15,'2026-07-30 17:50:46'),(13,30,1,16,'2026-07-31 19:57:35'),(14,32,1,18,'2026-08-03 16:46:54'),(15,33,1,19,'2026-08-30 16:44:19');
/*!40000 ALTER TABLE `purchases` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tokens`
--

DROP TABLE IF EXISTS `tokens`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tokens` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `token` varchar(512) NOT NULL,
  `expires_at` datetime NOT NULL,
  `is_revoked` tinyint(1) NOT NULL DEFAULT '0',
  `created_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`),
  KEY `ix_tokens_expires_at` (`expires_at`),
  KEY `ix_tokens_user_id` (`user_id`),
  CONSTRAINT `tokens_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=113 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tokens`
--

LOCK TABLES `tokens` WRITE;
/*!40000 ALTER TABLE `tokens` DISABLE KEYS */;
INSERT INTO `tokens` VALUES (111,16,'Kojiu8cyp560QMpXh-BpzWlTMW2Q7TFOtK4FCgH-WJ8rVrBEvx8ITTMQZ--WCY564HMvIeLAjbf6ws7hpXqNwg','2026-09-15 16:20:55',0,'2026-09-08 16:20:55'),(112,16,'FXRIPHZAL9841RFM3vI3j4q-AgDm0JVBRacm6P0uG8dkzSxIYk9YBLa0IOwSh5YFeg5NR7SMOZ1kZ-XzWiSUJQ','2026-09-15 17:42:00',0,'2026-09-08 17:42:00');
/*!40000 ALTER TABLE `tokens` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `email` varchar(255) NOT NULL,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `hashed_password` varchar(255) NOT NULL,
  `is_active` tinyint(1) NOT NULL DEFAULT '1',
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'test@example.com','Test','User','$2b$12$Ldz4cNfvF71X1F/dN6ica.EHySUXze4dmuDdAIEci6Laq0tVay7Je',1,'2026-06-22 03:00:01','2026-06-22 03:00:01'),(2,'jane@example.com','Jane','Doe','$2b$12$LkORSv1rKUs5aqhIDolFVenKJgnVMxixZv56geARjamadPLnW2uaa',1,'2026-06-22 03:00:01','2026-06-22 03:00:01'),(3,'alex.rivera@example.com','Alex','Rivera','$2b$12$NsFvLurNaFWdMiBoqX9R3.uNa1rEb9QmfXiwkqbi8Z7eFu.MOk.IW',1,'2026-06-22 03:00:01','2026-06-22 03:00:01'),(4,'sam.chen@example.com','Sam','Chen','$2b$12$lBUeT/1BHmCNMCfvD0v/E.DUrNeLboBvg8y9KAFgllMNem2rfiy2e',1,'2026-06-22 03:00:01','2026-06-22 03:00:01'),(5,'maria.gomez@example.com','Maria','Gomez','$2b$12$dS.dtpkT08cpMPBaJaRtKuinQeGcwj26Y5yOQKtAXropga5owQt0S',1,'2026-06-22 03:00:01','2026-06-22 03:00:01'),(10,'qwer@gmail.com','test','test','$2b$12$HspqVnTh9yxkw.eWyj4LVeRnT.YU8urvMC6RVI7ENpSoZM07XeAoC',1,'2026-06-24 17:45:35','2026-06-24 17:45:35'),(15,'q@gmail.com','asdf','asdf','$2b$12$IYIGeUtvhum0Z5snuBVnVuvrjw/XfY38dedjEQUs3RqFrkUZWwLZK',1,'2026-06-28 22:23:35','2026-06-28 22:23:35'),(16,'jaeyseo0922@gmail.com','jae','seo','$2b$12$XeA6WFu3m/RLq.JZsrV3Z.Kig1O921.vXY.PRcfsI2zx4B7Ovzaqq',1,'2026-06-29 02:47:42','2026-08-07 22:16:30'),(17,'robyn.meisinger@gmail.com','Robyn ','Meisinger','$2b$12$dDBevPO7duOTCnEaMCOKpekn82zdVS6ufBqesetlEfnPkA/T.hJie',1,'2026-06-29 04:05:25','2026-06-29 04:05:25'),(18,'abc@gmail.com','New','Test','$2b$12$WPVs5B1DDJg5jmmWH9Wf6uwvoQ.6s90ExlCEjqAtbvdEAcas4tzMq',1,'2026-06-29 16:45:03','2026-06-29 16:45:03'),(19,'trboccuzzi@gmail.com','Thomas','B','$2b$12$eCgbiioFBUhOGxtXSLFDpumJ1.tNySqln2zH0hhzx1N28539Np4x.',1,'2026-06-30 00:06:05','2026-06-30 00:06:05'),(20,'roselynmanderson@gmail.com','Rosie','Anderson','$2b$12$ObNe.L2m7ZhWFEof8cFw/uRYiUW5vHViATQKu7jhoYCAuZR/nfurm',1,'2026-06-30 04:03:11','2026-06-30 04:03:11'),(21,'0onlinemessage@gmail.com','Kim','O','$2b$12$PZ2zooXNpYxSCkjcxzm/guaKca17aOxitnZo9oCzcPpQS2Hu/SJ7q',1,'2026-06-30 12:56:52','2026-06-30 12:56:52'),(22,'angelique.gorospe@gmail.com','Angelique ','Guevarra ','$2b$12$9NWl4lmxDmZdrnWmQ8JtAucKhlLA.5LQLbFlD/sz4xuTwSzEfAJ46',1,'2026-07-02 04:26:25','2026-07-02 04:26:25'),(23,'nycurly@hotmail.com','Patricia ','Miranda ','$2b$12$2dM8SqKlInzXpIALdQ9cEumtRyiDAJB9HpRgckJijTDBsQJoDcHsy',1,'2026-07-06 04:53:06','2026-07-06 04:53:06'),(24,'ymbrown1976@gmail.com','Yvette','Brown','$2b$12$GnQ81Y0/VPVDTlWh23jrwun.RKfhBbAh1tcKbjL6ecns0I5IFjXw2',1,'2026-07-11 15:47:22','2026-07-11 15:47:22'),(25,'heidi.farrell64@yahoo.com','Heidi','Farrell ','$2b$12$mCjgLydsVqKLTZiGvKLNj.3KC3Ap/O9SRT65KY90ixElvLLRBeqwm',1,'2026-07-19 00:11:00','2026-07-19 00:11:00'),(26,'trishakee08@gmail.com','Trisha','Lacroix','$2b$12$AvXAog6u2JnC.z0g6PIBwOJ/npwzyavJLvj9lTBXwZgIRviwXo71G',1,'2026-07-19 18:54:54','2026-07-19 18:54:54'),(27,'bethk12@gmail.com','beth','kaufman','$2b$12$M/DLQOXTWNvIRPvEdsE7R.U9n5QWPDgQuvSsp1UifNDOvBQKXCwqq',1,'2026-07-22 22:21:26','2026-07-22 22:21:26'),(28,'thypham502@gmail.com','Thy','Pham','$2b$12$VajvaaT2hAc4MJfi8jlkWOMRHMrcrVW/aaaZ5R/jAx0syU5sgq15G',1,'2026-07-30 17:50:03','2026-07-30 17:50:03'),(30,'test@test.com','test','test','$2b$12$8ghS/XA1u/DCA9PURAn6DeHmQMlUyC4qpuPajp0pqt3FUb7pBjNju',1,'2026-07-31 19:57:14','2026-07-31 19:57:14'),(31,'test@gmail.com','new','testing','$2b$12$12CJZqbuI03C5jib.8zHqOdJmUaaqz3/klwtNT3PjvIcuVFpe1H0y',1,'2026-08-02 06:49:55','2026-08-02 06:49:55'),(32,'irene.aizenberg@gmail.com','Irene','Aizenberg','$2b$12$dmZPsuwkyM1M8e1ug4bQWO3Z/3/2FzoTvI/XgSgY8vLcsq22mkxKS',1,'2026-08-03 16:46:28','2026-08-03 16:46:28'),(33,'alexacorrea1209@gmail.com','Alexa','Correa','$2b$12$efZAhZZRtjAiRB/xlXNDXOVjuWI/JOrEw3NTaZH4z1g2p4Zc2IZwO',1,'2026-08-30 16:44:00','2026-08-30 16:44:00');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `waitlist_entries`
--

DROP TABLE IF EXISTS `waitlist_entries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `waitlist_entries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `map_id` int NOT NULL,
  `status` enum('pending','notified','joined') NOT NULL DEFAULT 'pending',
  `notified_at` datetime DEFAULT NULL,
  `created_at` datetime NOT NULL DEFAULT (now()),
  `updated_at` datetime NOT NULL DEFAULT (now()),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_waitlist_entries_user_map` (`user_id`,`map_id`),
  KEY `ix_waitlist_entries_user_id` (`user_id`),
  KEY `ix_waitlist_entries_map_id` (`map_id`),
  KEY `ix_waitlist_entries_status` (`status`),
  CONSTRAINT `waitlist_entries_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
  CONSTRAINT `waitlist_entries_ibfk_2` FOREIGN KEY (`map_id`) REFERENCES `maps` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `waitlist_entries`
--

LOCK TABLES `waitlist_entries` WRITE;
/*!40000 ALTER TABLE `waitlist_entries` DISABLE KEYS */;
INSERT INTO `waitlist_entries` VALUES (5,16,2,'pending',NULL,'2026-08-07 22:05:11','2026-08-07 22:05:11'),(6,16,3,'pending',NULL,'2026-08-07 22:11:41','2026-08-07 22:11:41');
/*!40000 ALTER TABLE `waitlist_entries` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-09-09 21:45:02
