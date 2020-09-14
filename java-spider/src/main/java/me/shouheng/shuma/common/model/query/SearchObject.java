package me.shouheng.shuma.common.model.query;

import lombok.Data;
import lombok.ToString;

import java.io.Serializable;
import java.util.LinkedList;
import java.util.List;

/**
 * 用来查询的对象
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  20:31
 */
@Data
@ToString
public class SearchObject implements Pageable, Sortable, Serializable {

    private static final long serialVersionUID = 4009650343975989289L;

    private Integer currentOffset;

    private Integer currentPage;

    private Integer pageSize;

    private List<Sort> sorts = new LinkedList<>();

    @Override
    public Integer getCurrentPage() {
        return currentPage;
    }

    @Override
    public void setCurrentPage(Integer currentPage) {
        this.currentPage = currentPage;
    }

    @Override
    public Integer getPageSize() {
        return pageSize;
    }

    @Override
    public void setPageSize(Integer pageSize) {
        this.pageSize = pageSize;
    }

    @Override
    public List<Sort> getSorts() {
        return sorts;
    }

    @Override
    public void addSort(Sort sort) {
        sorts.add(sort);
    }
}
