package me.shouheng.shuma.model.po;

import lombok.Data;
import lombok.EqualsAndHashCode;
import me.shouheng.shuma.anno.ColumnDefinition;
import me.shouheng.shuma.anno.TableDefinition;
import me.shouheng.shuma.common.model.AbstractPo;
import me.shouheng.shuma.model.enums.TopicType;

import javax.persistence.Column;
import javax.persistence.Table;
import java.util.Date;

/**
 * 话题数据实体
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019/8/18 22:54
 */
@Data
@Table(name = "gt_topic")
@TableDefinition(comment = "话题数据实体")
@EqualsAndHashCode(callSuper = true)
public class Topic extends AbstractPo {

    @Column(name = "name", nullable = false)
    @ColumnDefinition(comment = "名称")
    private String name;

    @Column(name = "type", nullable = false)
    @ColumnDefinition(comment = "话题类型", added = true)
    private TopicType type;

    @Column(name = "cover")
    @ColumnDefinition(comment = "封面")
    private String cover;

    @Column(name = "description")
    @ColumnDefinition(comment = "描述")
    private String description;

    @Column(name = "creator_id", nullable = false)
    @ColumnDefinition(comment = "创建者 id")
    private Long creatorId;

    @Column(name = "creator_name", nullable = false)
    @ColumnDefinition(comment = "创建者昵称")
    private String creatorName;

    @Column(name = "creator_avatar")
    @ColumnDefinition(comment = "创建者头像")
    private String creatorAvatar;

    @Column(name = "start_time", nullable = false)
    @ColumnDefinition(comment = "话题的开始时间", added = true)
    private Date startTime;

    @Column(name = "end_time", nullable = false)
    @ColumnDefinition(comment = "话题的结束时间", added = true)
    private Date endTime;
}
