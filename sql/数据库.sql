--创建分类表 gt_channel
CREATE TABLE IF NOT EXISTS gt_channel (
id BIGINT UNSIGNED NOT NULL COMMENT '记录的 ID',
name VARCHAR(255) NOT NULL COMMENT '名称',
parent_id BIGINT UNSIGNED COMMENT '父品类 id',
cat VARCHAR(255) NOT NULL COMMENT '京东品类的 cat',
treepath VARCHAR(255) NOT NULL COMMENT '品类的路径',
jdurl VARCHAR(255) COMMENT '京东链接',
tburl VARCHAR(255) COMMENT '淘宝链接',
max_page_count INT UNSIGNED COMMENT '最大爬取的页数，用来根据分类进行个性定制',
handling_time BIGINT UNSIGNED COMMENT '处理时间',
display_order INT UNSIGNED NOT NULL COMMENT '展示的顺序',
remark VARCHAR(255) COMMENT '记录的备注信息',
lock_version BIGINT UNSIGNED NOT NULL COMMENT '乐观锁',
updated_time BIGINT UNSIGNED NOT NULL COMMENT '最后更新时间',
created_time BIGINT UNSIGNED NOT NULL COMMENT '创建时间') COMMENT '商品品类';
--添加主键 
ALTER TABLE gt_channel MODIFY id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT;
--修改自增主键 
ALTER TABLE gt_channel AUTO_INCREMENT = 66;

--创建商品条目表 gt_item
CREATE TABLE IF NOT EXISTS gt_item (
id BIGINT UNSIGNED NOT NULL COMMENT '记录的 ID',
name VARCHAR(500) COMMENT '名称',
promo VARCHAR(500) COMMENT '提示文字',
link VARCHAR(500) COMMENT '链接地址',
image VARCHAR(500) COMMENT '封面图片地址',
price BIGINT COMMENT '价格，乘以 100',
price_type VARCHAR(255) COMMENT '价格类型',
icons VARCHAR(255) COMMENT '标签',
source INT COMMENT '商品的来源',
parameters VARCHAR(3000) COMMENT '产品参数，json 结构',
packages VARCHAR(3000) COMMENT '包装参数，json 结构',
sku_id VARCHAR(255) COMMENT 'sku id',
product_id VARCHAR(255) COMMENT 'prodcut id',
vender_id VARCHAR(255) COMMENT 'vender id',
comment_count INT UNSIGNED COMMENT '评论总数',
average_score INT UNSIGNED COMMENT '平均得分',
good_rate INT UNSIGNED COMMENT '好评率，乘以 100',
comment_detail VARCHAR(255) COMMENT '评论信息，json 格式',
store VARCHAR(255) COMMENT '商店信息',
store_link VARCHAR(500) COMMENT '商店的链接',
brand VARCHAR(255) COMMENT '品牌名称',
brand_link VARCHAR(500) COMMENT '品牌的链接',
channel_id BIGINT UNSIGNED COMMENT '记录的 Channel ID',
channel VARCHAR(255) COMMENT '分类名称',
remark VARCHAR(255) COMMENT '记录的备注信息',
lock_version BIGINT UNSIGNED NOT NULL COMMENT '乐观锁',
handling_time BIGINT UNSIGNED COMMENT '处理时间',
updated_time BIGINT UNSIGNED NOT NULL COMMENT '最后更新时间',
created_time BIGINT UNSIGNED NOT NULL COMMENT '创建时间') COMMENT '商品条目';
--添加主键 
ALTER TABLE gt_item MODIFY id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT;
--修改自增主键 
ALTER TABLE gt_item AUTO_INCREMENT = 66;
--为链接添加索引
ALTER TABLE gt_item ADD INDEX(`link`);

--创建商品品牌表 gt_brand
CREATE TABLE IF NOT EXISTS gt_brand (
id BIGINT UNSIGNED NOT NULL COMMENT '记录的 ID',
name VARCHAR(500) NOT NULL COMMENT '名称',
data_initial VARCHAR(255) NOT NULL COMMENT '字母缩写',
logo VARCHAR(500) NOT NULL COMMENT '图标的链接地址',
link VARCHAR(500) NOT NULL COMMENT '商店的链接地址',
display_order INT UNSIGNED NOT NULL COMMENT '展示的顺序',
channel_id BIGINT UNSIGNED NOT NULL COMMENT '记录的 Channel ID',
channel VARCHAR(255) NOT NULL COMMENT '分类名称',
remark VARCHAR(255) COMMENT '记录的备注信息',
lock_version BIGINT UNSIGNED NOT NULL COMMENT '乐观锁',
updated_time BIGINT UNSIGNED NOT NULL COMMENT '最后更新时间',
created_time BIGINT UNSIGNED NOT NULL COMMENT '创建时间') COMMENT '商品品牌';
--添加主键 
ALTER TABLE gt_brand MODIFY id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT;
--修改自增主键 
ALTER TABLE gt_brand AUTO_INCREMENT = 66;
--为链接添加索引
ALTER TABLE gt_brand ADD INDEX(`link`);

--创建商品的折扣表
CREATE TABLE IF NOT EXISTS gt_discount (
id BIGINT UNSIGNED NOT NULL COMMENT '记录的 ID',
goods_id BIGINT UNSIGNED COMMENT '商品的 ID',
batch_id VARCHAR(255) COMMENT '折扣的唯一标识',
quota BIGINT COMMENT '条件金额，乘以 100',
discount BIGINT COMMENT '折扣金额，乘以 100',
start_time BIGINT UNSIGNED COMMENT '折扣的开始时间',
end_time BIGINT UNSIGNED COMMENT '折扣的结束时间',
remark VARCHAR(255) COMMENT '记录的备注信息',
lock_version BIGINT UNSIGNED NOT NULL COMMENT '乐观锁',
updated_time BIGINT UNSIGNED NOT NULL COMMENT '最后更新时间',
created_time BIGINT UNSIGNED NOT NULL COMMENT '创建时间') COMMENT '商品折扣';
--添加主键 
ALTER TABLE gt_discount MODIFY id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT;
--修改自增主键 
ALTER TABLE gt_discount AUTO_INCREMENT = 66;


