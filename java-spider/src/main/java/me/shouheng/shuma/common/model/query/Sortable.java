package me.shouheng.shuma.common.model.query;

import java.util.List;

/**
 * 排序相关
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  20:32
 */
public interface Sortable {

    List<Sort> getSorts();

    void addSort(Sort sort);

}
