package me.shouheng.shuma.common.model.query;

/**
 * 分页相关
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  20:31
 */
public interface Pageable {

    Integer getCurrentPage();

    void setCurrentPage(Integer currentPage);

    Integer getPageSize();

    void setPageSize(Integer pageSize);

}
