package me.shouheng.shuma.common.model.query;

import lombok.Data;

import java.io.Serializable;

/**
 * 排序对象
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  20:32
 */
@Data
public class Sort implements Serializable {

    private static final long serialVersionUID = 7739709965769082011L;

    private String sortKey;

    private String sortDir;

    /**
     * 指定的键的“升序”排列
     *
     * @param sortKey 键
     * @return        排序实例
     */
    public static Sort of(String sortKey) {
        return new Sort(sortKey);
    }

    /**
     * 指定的键和方向排序
     *
     * @param sortKey 键
     * @param dir     排序方向
     * @return        排序实例
     */
    public static Sort of(String sortKey, Dir dir) {
        return new Sort(sortKey, dir.value);
    }

    public Sort() {
    }

    private Sort(String sortKey) {
        this.sortKey = sortKey;
    }

    private Sort(String sortKey, String sortDir) {
        this.sortKey = sortKey;
        this.sortDir = sortDir;
    }

    /**
     * 排序方向的枚举值
     */
    public enum Dir {
        /**
         * 升序：使用空代表升序
         */
        ASC(""),
        /**
         * 降序
         */
        DESC("DESC");

        public final String value;

        Dir(String value) {
            this.value = value;
        }
    }
}
