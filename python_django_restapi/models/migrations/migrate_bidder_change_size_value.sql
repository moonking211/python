SET @size_new_value = NULL;
SET @size_old_value = 'all';
UPDATE bidder_blacklist bl SET bl.size = @size_new_value WHERE bl.size = @size_old_value;
UPDATE bidder_whitelist wl SET wl.size = @size_new_value WHERE wl.size = @size_old_value;