package me.shouheng.shuma.common.model;

import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.List;

/**
 * 应用内部的结果包装实体
 *
 * @author <a href="mailto:shouheng2015@gmail.com">WngShhng</a>
 * @date 2019-08-01  23:32
 */
@Data
@NoArgsConstructor
public class PackVo<T>  {

    private static final long serialVersionUID = -2119661016457733317L;

    private boolean success = true;

    private T vo;

    private List<T> voList;

    private String code;

    private String message;

    /**
     * 备用字段
     */
    private Long udf1;

    /**
     * 备用字段
     */
    private Double udf2;

    /**
     * 备用字段
     */
    private Boolean udf3;

    /**
     * 备用字段
     */
    private String udf4;

    /**
     * 备用字段
     */
    private Object udf5;

    public static <E> PackVo<E> success() {
        return new PackVo<>();
    }

    public static <E> PackVo<E> success(E vo) {
        PackVo<E> packVo = new PackVo<>();
        packVo.setSuccess(true);
        packVo.setVo(vo);
        return packVo;
    }

    public static <E> PackVo<E> success(List<E> voList) {
        PackVo<E> packVo = new PackVo<>();
        packVo.setSuccess(true);
        packVo.setVoList(voList);
        return packVo;
    }

    public static <E> PackVo<E> fail() {
        PackVo<E> packVo = new PackVo<>();
        packVo.setSuccess(false);
        return packVo;
    }

    public static <E> PackVo<E> fail(String code, String message) {
        PackVo<E> packVo = new PackVo<>();
        packVo.setSuccess(false);
        packVo.setCode(code);
        packVo.setMessage(message);
        return packVo;
    }
}
