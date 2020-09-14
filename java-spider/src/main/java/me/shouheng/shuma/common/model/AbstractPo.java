package me.shouheng.shuma.common.model;

import lombok.Data;
import me.shouheng.shuma.anno.ColumnDefinition;

import javax.persistence.Column;
import javax.persistence.Id;
import javax.persistence.Version;
import java.io.Serializable;
import java.util.Date;

/**
 * 数据库对象的抽象基类
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019/7/31
 */
@Data
public abstract class AbstractPo implements Serializable {

    private static final long serialVersionUID = 6982434571375510313L;

    @Id
    @Column(name = "id", nullable = false)
    @ColumnDefinition(comment = "记录的 ID")
    private Long id;

    @Column(name = "remark")
    @ColumnDefinition(comment = "记录的备注信息")
    private String remark;

    @Version
    @Column(name = "lock_version", nullable = false)
    @ColumnDefinition(comment = "乐观锁")
    private Long lockVersion = 0L;

    @Column(name = "updated_time", nullable = false)
    @ColumnDefinition(comment = "记录的最后更新时间")
    private Date updatedTime;

    @Column(name = "created_time", nullable = false)
    @ColumnDefinition(comment = "记录的创建时间", genSchema = true)
    private Date createdTime;

}
