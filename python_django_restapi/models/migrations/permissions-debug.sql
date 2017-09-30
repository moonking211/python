-- DEBUG DATA===================================================================================================================
-- Users cleanup ---------------------------------------------------------------
DELETE FROM `auth_user` WHERE `id` IN (2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014);
DELETE FROM `auth_user_groups` WHERE `user_id` IN (2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014);
DELETE FROM `userprofile` WHERE `user_id` IN (2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014);
DELETE FROM `userprofile_trading_desks` WHERE `userprofile_id` IN (2001,2002,2003,2004,2005,2006,2007,2008,2009,2010,2011,2012,2013,2014);

UPDATE `auth_user` SET is_staff=1, is_superuser=1 WHERE username='sigma@manage.com';
SET @sigma_auth_user_id = (SELECT id FROM `auth_user` WHERE username='sigma@manage.com');
SET @sigma_profile_id = (SELECT id FROM userprofile WHERE user_id=@sigma_auth_user_id);
-- INSERT INTO `userprofile_trading_desks` SET userprofile_id=@sigma_profile_id, tradingdesk_id=1;

DELETE FROM `userprofile_advertisers` WHERE userprofile_id=@sigma_profile_id AND advertiser_id=29;
INSERT INTO `userprofile_advertisers` SET userprofile_id=@sigma_profile_id, advertiser_id=29;

SET @is_staff=1;
SET @password='pbkdf2_sha256$12000$iKN286Ld9wqd$iqz2Jh31Ni9GaF003CJuNr5PjTErpaAwKq//zWyAxbY=';

SET @username='td-stakeholder@manage.com';
INSERT INTO `auth_user` SET id=2001, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2001, user_id=2001;
INSERT INTO `auth_user_groups` SET user_id=2001, group_id=21;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2001, 2);

SET @username='td-campaign-supervisor@manage.com';
INSERT INTO `auth_user` SET id=2002, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2002, user_id=2002;
INSERT INTO `auth_user_groups` SET user_id=2002, group_id=22;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2002, 2);

SET @username='td-campaign-manager@manage.com';
INSERT INTO `auth_user` SET id=2003, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2003, user_id=2003;
INSERT INTO `auth_user_groups` SET user_id=2003, group_id=23;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2003, 2);

SET @username='td-account-manager@manage.com';
INSERT INTO `auth_user` SET id=2004, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2004, user_id=2004;
INSERT INTO `auth_user_groups` SET user_id=2004, group_id=24;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2004, 2);

SET @username='manage-stakeholder@manage.com';
INSERT INTO `auth_user` SET id=2005, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2005, user_id=2005;
INSERT INTO `auth_user_groups` SET user_id=2005, group_id=25;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2005, 1);

SET @username='manage-superuser@manage.com';
INSERT INTO `auth_user` SET id=2006, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2006, user_id=2006;
INSERT INTO `auth_user_groups` SET user_id=2006, group_id=26;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2006, 1);

SET @username='manage-adops-head@manage.com';
INSERT INTO `auth_user` SET id=2007, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2007, user_id=2007;
INSERT INTO `auth_user_groups` SET user_id=2007, group_id=27;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2007, 1);

SET @username='manage-adops-supervisor@manage.com';
INSERT INTO `auth_user` SET id=2008, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2008, user_id=2008;
INSERT INTO `auth_user_groups` SET user_id=2008, group_id=28;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2008, 1);

SET @username='manage-adops-analyst@manage.com';
INSERT INTO `auth_user` SET id=2009, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2009, user_id=2009;
INSERT INTO `auth_user_groups` SET user_id=2009, group_id=29;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2009, 1);

SET @username='manage-account-manager@manage.com';
INSERT INTO `auth_user` SET id=2010, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2010, user_id=2010;
INSERT INTO `auth_user_groups` SET user_id=2010, group_id=30;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2010, 1);

SET @username='manage-td-account-manager@manage.com';
INSERT INTO `auth_user` SET id=2011, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2011, user_id=2011;
INSERT INTO `auth_user_groups` SET user_id=2011, group_id=31;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2011, 1);

SET @username='manage-creative-approval@manage.com';
INSERT INTO `auth_user` SET id=2012, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2012, user_id=2012;
INSERT INTO `auth_user_groups` SET user_id=2012, group_id=32;
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) VALUES (2012, 1);

SET @username='advertiser@manage.com';
INSERT INTO `auth_user` SET id=2013, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2013, user_id=2013;
INSERT INTO `auth_user_groups` SET user_id=2013, group_id=33;

SET @username='publisher@manage.com';
INSERT INTO `auth_user` SET id=2014, password=@password, username=@username, email=@username, is_active=1, is_staff=@is_staff, date_joined=NOW();
INSERT INTO `userprofile` SET id=2014, user_id=2014;
INSERT INTO `auth_user_groups` SET user_id=2014, group_id=34;

-- UPDATE User's ================================================================================================================
INSERT INTO `userprofile` (user_id) SELECT id FROM `auth_user` WHERE id NOT IN (SELECT user_id FROM `userprofile`);
INSERT INTO `userprofile_trading_desks` (userprofile_id, tradingdesk_id) SELECT id, 1 FROM `userprofile` WHERE id NOT IN (SELECT userprofile_id FROM `userprofile_trading_desks`);
